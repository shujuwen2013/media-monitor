# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponseBadRequest, HttpResponse
from django import forms
from django.contrib import messages
from django.conf import settings

import django_excel as excel

from utils import tokenize_text

import pandas as pd


#import time
# Create your views here.

class UploadFileForm(forms.Form):
    file = forms.FileField()


def index(request):

	if request.method == "POST":

		try:
			storage = messages.get_messages(request)
			for message in storage:
				print message
			storage.used = True
		except:
			pass

    	form = UploadFileForm(request.POST, request.FILES)
    	if form.is_valid():
			try:
				filehandle = request.FILES['file']
				xls = pd.ExcelFile(filehandle)
				df = xls.parse('Sheet1')
				par =xls.parse('Sheet2').values.transpose()
				df = process(df, par)
			except Exception as e:
				print e
				messages.warning(request, 'The uploaded file has some problems: ' + str(e))
				return render(
        			request,
        			'scanner/index.html',
        			{
            			'form': form,
        			})
			return excel.make_response_from_array(
        		[df.columns.values.tolist()] + df.as_matrix().tolist(),
        		"xls",
        		file_name="download",
        		)
	else:
		form = UploadFileForm()
	return render(
        request,
        'scanner/index.html',
        {
            'form': form,
        })


def process(df, par):
	# tokenize columns
	df['Tokenized_Title'] = df['Title'].apply(tokenize_text)
	#df['Tokenized_Content'] = df['Content'].apply(tokenize_text)

	# define parameter lists
	# v==v will filter out NaN values
	target_titles = [v for v in par[0] if v==v]
	tokenized_target_titles = map(tokenize_text, target_titles)
	brands = [v for v in par[1] if v==v]
	competitors = [v for v in par[2] if v==v]
	keywords = [v for v in par[3] if v==v]
	web_exceptions = [v for v in par[4] if v==v]
	
	# measure title score
	def score_title(text):
		score = 0
		if len(set(text)) > 0:
			text = text[0:30]
			for l in tokenized_target_titles:
				l = l[0:30]
				s = len(set(text) & set(l))
				if (s*1.0/len(set(l)) + s*1.0/len(set(text)))/2 > score:
					score = (s*1.0/len(set(l)) + s*1.0/len(set(text)))/2
		return score

	# count words in content
	def count_word(token_list, candidates):
		num = 0
		for c in candidates:
			num = num + token_list.count(c.lower())
		return num

	# define exceptional url pattern
	def is_web_exception(url):
		for e in web_exceptions:
			if url.startswith(e):
				return True
		return False


	# calculate results
	df['Title_Similarity'] = df['Tokenized_Title'].apply(score_title)

	df['Brand_Count_Title'] = df['Tokenized_Title'].apply(lambda x: count_word(x, brands))
	df['Brand_Rate_Title'] = df['Brand_Count_Title']/df['Tokenized_Title'].apply(lambda x: len(x) + 0.01)

	df['Competitor_Count_Title'] = df['Tokenized_Title'].apply(lambda x: count_word(x, competitors))
	df['Competitor_Rate_Title'] = df['Competitor_Count_Title']/df['Tokenized_Title'].apply(lambda x: len(x) + 0.01)

	df['Brand_Dominate_Title'] =  df['Brand_Rate_Title'] - df['Competitor_Rate_Title']

	df['KW_Count_Title'] = df['Tokenized_Title'].apply(lambda x: count_word(x, keywords))
	df['KW_Rate_Title'] = df['KW_Count_Title']/df['Tokenized_Title'].apply(lambda x: len(x) + 0.01)

	#df['Brand_Count_Content'] = df['Tokenized_Content'].apply(lambda x: count_word(x, brands))
	#df['Brand_Rate_Content'] = df['Brand_Count_Content']/df['Tokenized_Content'].apply(lambda x: len(x) + 0.01)

	#df['Competitor_Count_Content'] = df['Tokenized_Content'].apply(lambda x: count_word(x, competitors))
	#df['Competitor_Rate_Content'] = df['Competitor_Count_Content']/df['Tokenized_Content'].apply(lambda x: len(x) + 0.01)

	#df['Brand_Dominate_Content'] =  df['Brand_Rate_Content'] - df['Competitor_Rate_Content']

	#df['KW_Count_Content'] = df['Tokenized_Content'].apply(lambda x: count_word(x, keywords))
	#df['KW_Rate_Content'] = df['KW_Count_Content']/df['Tokenized_Content'].apply(lambda x: len(x) + 0.01)

	df['Is_Web_Exception'] = df['URL'].apply(is_web_exception)

	df['Category'] = df.apply(
		lambda row: categorize(
			row['Title_Similarity'], 
			row['Brand_Rate_Title'], 
			row['Brand_Dominate_Title'], 
			row['KW_Rate_Title'], 
			row['Is_Web_Exception']), axis=1)

	df = df.drop('Tokenized_Title', axis=1)
	#df = df.drop('Tokenized_Content', axis=1)


	# move column 'Category' to last
	cate = df['Category']
	df.drop(labels=['Category'], axis=1, inplace = True)
	df.insert(len(df.columns.values), 'Category', cate)
	
	return df


def categorize(title_similarity, brand_rate, brand_dominate, kw_rate, web_exception):
	if title_similarity > 0.85:
		return 1
	elif web_exception:
		if brand_rate > 0 and brand_dominate >= -0.001 and kw_rate >= 0.15:
			return 2
		else:
			return 3
	else:
		if brand_rate==0 or brand_dominate < 0.001 or kw_rate < 0.025:
			return 3
		elif title_similarity > 0.65:
			return 1
		else:
			return 2

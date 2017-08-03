# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponseBadRequest, HttpResponse
from django import forms
from django.contrib import messages
from django.conf import settings

import django_excel as excel

from utils import tokenize_text
from utils import categorize_sony
from utils import process_sony
from utils import process_samsung

import pandas as pd


#import time
# Create your views here.

class UploadFileForm(forms.Form):
    file = forms.FileField()


def sony(request):

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
				df = process_sony(df, par)
			except Exception as e:
				print e
				messages.warning(request, 'The uploaded file has some problems: ' + str(e))
				return render(
        			request,
        			'scanner/sony.html',
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
        'scanner/sony.html',
        {
            'form': form,
        })


def samsung(request):
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
				df = process_samsung(df, par)
			except Exception as e:
				print e
				messages.warning(request, 'The uploaded file has some problems: ' + str(e))
				return render(
        			request,
        			'scanner/samsung.html',
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
        'scanner/samsung.html',
        {
            'form': form,
        })

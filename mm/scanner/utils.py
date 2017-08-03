# -*- coding: utf-8 -*-

import jieba.posseg as pseg
import jieba


# tokenization without punctuations 
def tokenize_text(text):
    # adjust dictionary
    jieba.suggest_freq(('看', '电视'), True)
    jieba.add_word('量子点', freq=100, tag='n')
    jieba.add_word('光质', freq=100, tag='n')
    # cut words
    nv_words = []
    for word, flag in pseg.cut(text):
        # http://blog.csdn.net/li_31415/article/details/48660073
        if flag[0] not in 'x':
        #print('%s %s' % (word, flag))
            nv_words.append(word.lower())
    return nv_words


# categorization for Sony
def categorize_sony(title_similarity, brand_rate, brand_dominate, kw_rate, fw_count, is_weixin):    
    if title_similarity > 0.85:
        return 'published'
    if not is_weixin and \
        title_similarity > 0.65 and \
        brand_rate > 0 and \
        brand_dominate >= 0.001 and \
        kw_rate >= 0.025 and \
        fw_count == 0:
        return 'published'

    if is_weixin and \
        brand_rate > 0 and \
        brand_dominate >= -0.001 and \
        kw_rate >= 0.15 and \
        fw_count == 0:
        return 'relevant'
    if not is_weixin and \
        title_similarity <= 0.65 and \
        brand_rate > 0 and \
        brand_dominate >= 0.001 and \
        kw_rate > 0.025 and \
        fw_count == 0:
        return 'relevant'

    return 'irrelevant'
       

# calculate metrics for Sony
def process_sony(df, par, debug=True):
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
    forbidden_words = [v for v in par[4] if v==v]

    # define other parameters
    weibo = ['http://t.sina.com.cn/']
    weixin = ['http://mp.weixin.qq.com']  
    
    # measure title score
    def score_title(text):
        score = 0
        if len(set(text)) > 0:
            text = text[0:30]
            for l in tokenized_target_titles:
                l = l[0:30]
                if len(l) > 0:
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

    # recgnize patterns in url
    def rec_web(url, pattern):
        for e in pattern:
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

    df['FW_Count_Title'] = df['Tokenized_Title'].apply(lambda x: count_word(x, forbidden_words))

    df['Is_Weixin'] = df['URL'].apply(lambda x: rec_web(x, weixin))
    

    df['Category'] = df.apply(
        lambda row: categorize_sony(
            row['Title_Similarity'], 
            row['Brand_Rate_Title'], 
            row['Brand_Dominate_Title'], 
            row['KW_Rate_Title'],
            row['FW_Count_Title'],
            row['Is_Weixin']), axis=1)

    # clean data
    if not debug:
        df = df.drop('Tokenized_Title', axis=1)
        df = df.drop('Title_Similarity', axis=1)
        df = df.drop('Brand_Count_Title', axis=1)
        df = df.drop('Brand_Rate_Title', axis=1)
        df = df.drop('Competitor_Count_Title', axis=1)
        df = df.drop('Competitor_Rate_Title', axis=1)
        df = df.drop('Brand_Dominate_Title', axis=1)
        df = df.drop('KW_Count_Title', axis=1)
        df = df.drop('KW_Rate_Title', axis=1)
        df = df.drop('FW_Count_Title', axis=1)
        df = df.drop('Is_Weixin', axis=1)

    # move column 'Category' to last
    cate = df['Category']
    df.drop(labels=['Category'], axis=1, inplace = True)
    df.insert(len(df.columns.values), 'Category', cate)
    
    return df

# categorization for Samsung
def categorize_samsung(sim_num_title, brand_rate, brand_dominate, kw_rate, fw_count, is_weibo, sentiment):
    if not sentiment.endswith('Negative'):
        if not is_weibo and \
            sim_num_title >= 2 and \
            brand_rate > 0 and \
            brand_dominate >= -0.001 and \
            kw_rate >= 0.025 and \
            fw_count == 0:
            return 'published'          
    if brand_rate > 0 and kw_rate >= 0.025 and fw_count == 0:
        return 'relevant' 
    return 'irrelevant'


# calculate metrics for Samsung
def process_samsung(df, par, debug=False):
    # tokenize columns
    df['Tokenized_Title'] = df['Title'].apply(tokenize_text)
    #df['Tokenized_Content'] = df['Content'].apply(tokenize_text)

    # define parameter lists
    # v==v will filter out NaN values
    brands = [v for v in par[0] if v==v]
    competitors = [v for v in par[1] if v==v]
    keywords = [v for v in par[2] if v==v]
    forbidden_words = [v for v in par[3] if v==v]

    # define other parameters
    weibo = ['http://t.sina.com.cn/']
    weixin = ['http://mp.weixin.qq.com']  

    # measure title score
    def score_title_iter(text, target_text):
        scores  = []
        if len(text) > 0:
            text = text[0:15]
            for l in target_text:
                l = l[0:15]
                if len(l) > 0:
                    s = len(set(text) & set(l))
                    scores.append((s*1.0/len(set(l)) + s*1.0/len(set(text)))/2)
        return scores

    # count words in content
    def count_word(token_list, candidates):
        num = 0
        for c in candidates:
            num = num + token_list.count(c.lower())
        return num

    # recgnize patterns in url
    def rec_web(url, pattern):
        for e in pattern:
            if url.startswith(e):
                return True
        return False

    tokenized_titles_list = df['Tokenized_Title'].values.tolist()
    df['Sim_Scores_Title'] = df['Tokenized_Title'].apply(lambda x: score_title_iter(x, tokenized_titles_list))
    df['Sim_Num_Title'] = df['Sim_Scores_Title'].apply(lambda x: sum(float(num) >= 0.75 for num in x))

    df['Brand_Count_Title'] = df['Tokenized_Title'].apply(lambda x: count_word(x, brands))
    df['Brand_Rate_Title'] = df['Brand_Count_Title']/df['Tokenized_Title'].apply(lambda x: len(x) + 0.01)

    df['Competitor_Count_Title'] = df['Tokenized_Title'].apply(lambda x: count_word(x, competitors))
    df['Competitor_Rate_Title'] = df['Competitor_Count_Title']/df['Tokenized_Title'].apply(lambda x: len(x) + 0.01)

    df['Brand_Dominate_Title'] =  df['Brand_Rate_Title'] - df['Competitor_Rate_Title']

    df['KW_Count_Title'] = df['Tokenized_Title'].apply(lambda x: count_word(x, keywords))
    df['KW_Rate_Title'] = df['KW_Count_Title']/df['Tokenized_Title'].apply(lambda x: len(x) + 0.01)

    df['FW_Count_Title'] = df['Tokenized_Title'].apply(lambda x: count_word(x, forbidden_words))

    df['Is_Weixin'] = df['URL'].apply(lambda x: rec_web(x, weixin))
    df['Is_Weibo'] = df['URL'].apply(lambda x: rec_web(x, weibo))
    
    df['Category'] = df.apply(
        lambda row: categorize_samsung(
            row['Sim_Num_Title'], 
            row['Brand_Rate_Title'], 
            row['Brand_Dominate_Title'], 
            row['KW_Rate_Title'], 
            row['FW_Count_Title'],
            row['Is_Weibo'],
            row['Sentiment Score']), axis=1)

    # clean data
    df = df.drop('Sim_Scores_Title', axis=1)
    if not debug:
        df = df.drop('Tokenized_Title', axis=1)
        df = df.drop('Sim_Num_Title', axis=1)
        df = df.drop('Brand_Count_Title', axis=1)
        df = df.drop('Brand_Rate_Title', axis=1)
        df = df.drop('Competitor_Rate_Title', axis=1)
        df = df.drop('Brand_Dominate_Title', axis=1)
        df = df.drop('KW_Count_Title', axis=1)
        df = df.drop('KW_Rate_Title', axis=1)
        df = df.drop('FW_Count_Title', axis=1)
        df = df.drop('Is_Weixin', axis=1)
        df = df.drop('Is_Weibo', axis=1)
    
    # move column 'Category' to last
    cate = df['Category']
    df.drop(labels=['Category'], axis=1, inplace = True)
    df.insert(len(df.columns.values), 'Category', cate)
    
    return df

import pickle as pickle
import os
import pandas as pd
import torch
import re

class RE_Dataset(torch.utils.data.Dataset):
  """ Dataset 구성을 위한 class."""
  def __init__(self, pair_dataset, labels):
    self.pair_dataset = pair_dataset
    self.labels = labels

  def __getitem__(self, idx):
    item = {key: val[idx].clone().detach() for key, val in self.pair_dataset.items()}
    item['labels'] = torch.tensor(self.labels[idx])
    return item

  def __len__(self):
    return len(self.labels)

def last_preprocessing(dataset,mode=""):
  concat_entity=[]
  len_addtoken=0
  if mode=='typed_entity_marker':
    new_tokens=[]
    match_dict={
      'PER': '사람',
      'ORG':'조직',
      'DAT':'날짜',
      'LOC':'장소',
      'POH':'단어',#직업이 많아보이긴함 근데 완전다른것도 존재
      'NOH':'숫자'
    }
    for sen,e01,e02, ss,se,os,oe in zip(dataset['sentence'], dataset['subject_entity'],dataset['object_entity'],dataset['ss'],dataset['se'],dataset['os'],dataset['oe']):
      temp = ''
      subj_start = '[SUBJ-{}]'.format(e01)
      subj_end='[/SUBJ-{}]'.format(e01)
      obj_start='[OBJ-{}]'.format(e02)
      obj_end='[/OBJ-{}]'.format(e02)
      ss=int(ss)
      se=int(se)
      os=int(os)
      oe=int(oe)
      for token in (subj_start,subj_end,obj_start,obj_end):
        if token not in new_tokens:    
          new_tokens.append(token)
          tokenizer.add_tokens([token])
      
      if ss<=os:
        temp=sen[0:ss]+subj_start+sen[ss:se+1]+subj_end+sen[se+1:os]+obj_start+sen[os:oe+1]+obj_end+sen[oe+1:] 
      else:
        temp=sen[0:os]+obj_start+sen[os:oe+1]+obj_end+sen[oe+1:ss]+subj_start+sen[ss:se+1]+subj_end+sen[se+1:]
      temp = re.sub(r"[^ a-zA-Z0-9가-힣<>/.,!?;:()%\-\]\[]", " ", temp)
      print(temp)
      concat_entity.append(temp)
    len_addtoken=len(new_tokens)
    print(new_tokens)
    out_dataset = pd.DataFrame({'id':dataset['id'], 'sentence':concat_entity,'subject_entity':dataset['subject_entity'],'object_entity':dataset['object_entity'],'label':dataset['label'],})
  
  if mode=='typed_entity_marker_punct':
    match_dict={
      'PER': '사람',
      'ORG':'조직',
      'DAT':'날짜',
      'LOC':'장소',
      'POH':'단어',#직업이 많아보이긴함 근데 완전다른것도 존재
      'NOH':'숫자'
    }
    for sen,e01,e02, ss,se,os,oe in zip(dataset['sentence'], dataset['subject_entity'],dataset['object_entity'],dataset['ss'],dataset['se'],dataset['os'],dataset['oe']):
      temp = ''
      sub_entity=match_dict[e01]
      obj_entity=match_dict[e02]
      ss=int(ss)
      se=int(se)
      os=int(os)
      oe=int(oe)
        
      if ss<=os:
        temp=sen[0:ss]+"@*"+sub_entity+"*"+sen[ss:se+1]+"@"+sen[se+1:os]+"#^"+obj_entity+"^"+sen[os:oe+1]+"#"+sen[oe+1:] 
      else:
        temp=sen[0:os]+"#^"+obj_entity+"^"+sen[os:oe+1]+"#"+sen[oe+1:ss]+"@*"+sub_entity+"*"+sen[ss:se+1]+"@"+sen[se+1:]
      temp = re.sub(r"[^ a-zA-Z0-9가-힣<>/.,!?;:()%\-\]\[]", " ", temp)
      print(temp)
      concat_entity.append(temp)
    out_dataset = pd.DataFrame({'id':dataset['id'], 'sentence':concat_entity,'subject_entity':dataset['subject_entity'],'object_entity':dataset['object_entity'],'label':dataset['label'],})
  return out_dataset,len_addtoken

def preprocessing_dataset(dataset):
  """ 처음 불러온 csv 파일을 원하는 형태의 DataFrame으로 변경 시켜줍니다."""
  len_addtoken=0
  concat_entity=[]
  for sen,e01,e02, ss,se,os,oe in zip(dataset['sentence'], dataset['subject_entity'],dataset['object_entity'],dataset['ss'],dataset['se'],dataset['os'],dataset['oe']):
    sen=re.sub(r"[^ a-zA-Z0-9가-힣<>/.,!?;:()%\-\]\[]", " ", sen)
    concat_entity.append(sen)
  out_dataset = pd.DataFrame({'id':dataset['id'], 'sentence':dataset['sentence'],'subject_entity':dataset['subject_entity'],'object_entity':dataset['object_entity'],'label':dataset['label'],})
  return out_dataset,len_addtoken

def ner_preprocessing_dataset(dataset):
  """ 처음 불러온 csv 파일을 원하는 형태의 DataFrame으로 변경 시켜줍니다."""
  subject_entity = []
  object_entity = []
  ss_entity=[]
  se_entity=[]
  os_entity=[]
  oe_entity=[]
  sen_li=[]
  for i,j,sen in zip(dataset['subject_entity'], dataset['object_entity'],dataset['sentence']):
    sepi=i.split('start_idx')
    sepj=j.split('start_idx')
    ss,se=re.findall(r'[0-9]+',sepi[1])
    os,oe=re.findall(r'[0-9]+',sepj[1])
    i = i.split('\'type\': ')
    j = j.split('\'type\': ')
    i=re.search(r'[A-z]+',i[1]).group()
    j=re.search(r'[A-z]+',j[1]).group()
    #
    sen_li.append(new_sen)
    subject_entity.append(i)
    object_entity.append(j)
    ss_entity.append(ss)
    se_entity.append(se)
    os_entity.append(os)
    oe_entity.append(oe)
  out_dataset = pd.DataFrame({'id':dataset['id'], 'sentence':sen_li,'subject_entity':subject_entity,'object_entity':object_entity,'label':dataset['label'],'ss':ss_entity,'se':se_entity,'os':os_entity,'oe':oe_entity,})
  
  return out_dataset
def load_data(dataset_dir,datamode="adea",mode="typed_entity_marker_punct"):
  """ csv 파일을 경로에 맡게 불러 옵니다. """
  if datamode=="adea":#속도를 빠르게 하기위해 adea코드를 사용하지 않았다
    pd_dataset=pd.read_csv(dataset_dir)
    if mode="base":
      dataset,len_token=preprocessing_dataset(pd_dataset)
      return dataset,len_token
    else:
      dataset,len_token=last_preprocessing(pd_dataset,mode)
      return dataset,len_token
  elif datamode="basic":
    pd_dataset=pd.read_csv(dataset_dir)
    if mode="base":##사용하면 성능안좋을 확률 높다
      dataset,len_token=preprocessing_dataset(pd_dataset)
      return dataset,len_token
    else:
      dataset=ner_preprocessing_dataset(pd_dataset)
      dataset,len_token=last_preprocessing(dataset)
      return dataset,len_token
  else: 
    print("잘못된 데이터 모드입니다")
  return dataset


def tokenized_dataset(dataset, tokenizer,mode="PASS"):
  """ tokenizer에 따라 sentence를 tokenizing 합니다."""
  print(dataset.iloc[0])
  breakpoint()
  concat_entity = []
  if mode==None:
    for e01, e02 in zip(dataset['subject_entity'], dataset['object_entity']):
      temp = ''
      temp = e01 + '[SEP]' + e02
      concat_entity.append(temp)
  
  if mode=='typed_entity_marker':
    new_tokens=[]

    for sen,e01,e02, ss,se,os,oe in zip(dataset['sentence'], dataset['subject_entity'],dataset['object_entity'],dataset['ss'],dataset['se'],dataset['os'],dataset['oe']):
        temp = ''
        subj_start = '[SUBJ-{}]'.format(e01)
        subj_end='[/SUBJ-{}]'.format(e01)
        obj_start='[OBJ-{}]'.format(e02)
        obj_end='[/OBJ-{}]'.format(e02)
        ss=int(ss)
        se=int(se)
        os=int(os)
        oe=int(oe)
        for token in (subj_start,subj_end,obj_start,obj_end):
          if token not in new_tokens:    
            new_tokens.append(token)
            tokenizer.add_tokens([token])
        
        if ss<=os:
          temp=sen[0:ss]+subj_start+sen[ss:se+1]+subj_end+sen[se+1:os]+obj_start+sen[os:oe+1]+obj_end+sen[oe+1:] 
        else:
          temp=sen[0:os]+obj_start+sen[os:oe+1]+obj_end+sen[oe+1:ss]+subj_start+sen[ss:se+1]+subj_end+sen[se+1:]
        print(temp)
        concat_entity.append(temp)

  if mode=='typed_entity_marker_punct':

    match_dict={
      'PER': '사람',
      'ORG':'조직',
      'DAT':'날짜',
      'LOC':'장소',
      'POH':'단어',#직업이 많아보이긴함 근데 완전다른것도 존재
      'NOH':'숫자'
    }
    for sen,e01,e02, ss,se,os,oe in zip(dataset['sentence'], dataset['subject_entity'],dataset['object_entity'],dataset['ss'],dataset['se'],dataset['os'],dataset['oe']):
        temp = ''
        sub_entity=match_dict[e01]
        obj_entity=match_dict[e02]
        ss=int(ss)
        se=int(se)
        os=int(os)
        oe=int(oe)
        
        if ss<=os:
          temp=sen[0:ss]+"@*"+sub_entity+"*"+sen[ss:se+1]+"@"+sen[se+1:os]+"#^"+obj_entity+"^"+sen[os:oe+1]+"#"+sen[oe+1:] 
        else:
          temp=sen[0:os]+"#^"+obj_entity+"^"+sen[os:oe+1]+"#"+sen[oe+1:ss]+"@*"+sub_entity+"*"+sen[ss:se+1]+"@"+sen[se+1:]
        concat_entity.append(temp)
    if mode=="PASS":
      print(dataset['sentence'])
      breakpoint()
      tokenized_sentences = tokenizer(
      list(dataset['sentence']),
      return_tensors="pt",
      padding=True,
      truncation=True,
      max_length=256,
      add_special_tokens=True,
      )
      print(dataset['sentence'][0:0])
      #breakpoint()
      return tokenized_sentences
  tokenized_sentences = tokenizer(
      concat_entity,
      return_tensors="pt",
      padding=True,
      truncation=True,
      max_length=256,
      add_special_tokens=True,
      )
  input_ids=tokenized_sentences['input_ids'][0]
  
  return tokenized_sentences


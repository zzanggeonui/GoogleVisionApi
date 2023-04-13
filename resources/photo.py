import json
from flask_restful import Resource, reqparse
from io import BytesIO
from PIL import Image
from flask import Response, request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from mysql.connector import Error
import os
from google.oauth2 import service_account
from flask_jwt_extended import get_jwt_identity
import boto3
from config import Config
from datetime import datetime
from google.cloud import vision ,storage
import  os

key_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
client = storage.Client.from_service_account_json(key_path)

class VisionTextResource(Resource):

    def post(self):
        file = request.files['photo']
        content = file.read()


        client = vision.ImageAnnotatorClient()
        image =  vision.Image(content=content)
        response = client.text_detection(image=image)
        texts = response.text_annotations


        results = {'result': 'success', 'items': []}

        for i, text in enumerate(texts):
            if 'kcal' in text.description:
                vertices = text.bounding_poly.vertices
                prev_vertex = texts[i-2].bounding_poly.vertices[2] 
                kcal_text = texts[i-1].description     
                if prev_vertex.x < vertices[0].x:
                    for check in ['(', ':']:
                        if check in kcal_text: 
                            kcal_text = texts[i-2].description
                    #숫자만    
                    kcal_text = ''.join(filter(str.isdigit, kcal_text))
                    # 중복 확인 및 0 또는 "" 체크 , 2000kcal 기준이라는 안내문 추출 제거
                    if kcal_text != '2000' and kcal_text not in ['0', ' ']:
                        if not any(item.get('kcal', '') == kcal_text for item in results['items']):
                            results['items'].append({'kcal': kcal_text})

        #정말 열받게 숫자랑 kcal이란 글자가 딱붙어있는경우가 있음 그경우
        for i, text in enumerate(texts):
            if 'kcal' in text.description:
                words = text.description.split()
                for j in range(len(words)):
                    if 'kcal' in words[j]:
                        prev_word = words[j-1]
                        kcal_value = prev_word.replace(',', '')
                        kcal_value = ''.join(filter(str.isdigit, kcal_value))

                        if kcal_value != '2000' and kcal_value not in ['0', ' ']:                           
                            if not any(item.get('kcal', '') == kcal_value for item in results['items']):
                                results['items'].append({'kcal': kcal_value})

        for i, text in enumerate(texts):              
            if '탄수화물' in text.description:
                vertices = text.bounding_poly.vertices
                next_vertex = texts[i+1].bounding_poly.vertices[0]
                carbs_text = texts[i+1].description
                if next_vertex.x > vertices[2].x:
                    for check in ['(', ':']:
                        carbs_text = ''.join(filter(str.isdigit, carbs_text))
                    if carbs_text not in ['0', ' ']:
                        if not any(item.get('탄수화물', '')== carbs_text for item in results['items']):
                            results['items'].append({'탄수화물': carbs_text})

            elif '단백질' in text.description:
                vertices = text.bounding_poly.vertices
                next_vertex = texts[i+1].bounding_poly.vertices[0]
                protien_text = texts[i+1].description
                if next_vertex.x > vertices[2].x: 

                    for check in ['(', ':']:
                        if check in protien_text: 
                            protien_text = texts[i+2].description 
                        protien_text = ''.join(filter(str.isdigit, protien_text))
                    if protien_text not in ['0', ' ']:
                        if not any(item.get('단백질', '') == protien_text for item in results['items']):
                            results['items'].append({'단백질': protien_text})

            elif '내용량' in text.description:
                vertices = text.bounding_poly.vertices
                next_vertex = texts[i+1].bounding_poly.vertices[0]
                gram_text = texts[i+1].description
                if next_vertex.x > vertices[2].x: 
                    for check in ['(', ':']:
                        if check in gram_text: 
                            gram_text = texts[i+2].description 
                        gram_text = ''.join(filter(str.isdigit, gram_text))   
                        
                    if gram_text not in ['0', ' ']:                            
                        if not any(item.get('내용량', '') == gram_text for item in results['items']):        
                            results['items'].append({'gram': gram_text})
            #정말 열받지만 제공량이라고 적는 곳도 있음
            elif '제공량' in text.description:
                vertices = text.bounding_poly.vertices
                next_vertex = texts[i+1].bounding_poly.vertices[0] 
                gram_text = texts[i+1].description
                if next_vertex.x > vertices[2].x: 

                    for check in ['(', ':']:
                        if check in gram_text:
                            gram_text = texts[i+2].description
                        gram_text = ''.join(filter(str.isdigit, gram_text))  
                    if gram_text not in ['0', ' ']:                            
                        if not any(item.get('내용량', '') == gram_text for item in results['items']):        
                            results['items'].append({'gram': gram_text})
                            
             
         # 이상하게 트랜스지방과 포화지방은 아예description에서 찾지못함 이유는모름...그래서 트랜스글자좌표에서1칸(지방) 또1칸(숫자)              
         # 지방의 경우 3가지의 지방을 다 따로 부른뒤 fat_text에 트랜스지방과 포화지방 데이터 제거해줌
        for i, text in enumerate(texts):    
            if '트랜스' in text.description:
                vertices = text.bounding_poly.vertices
                next_vertex = texts[i+2].bounding_poly.vertices[0] 
                trans_text = texts[i+2].description
                if next_vertex.x > vertices[2].x: 

                    for check in ['(', ':']:
                        if check in trans_text:
                            trans_text = texts[i+2].description
                        trans_text = ''.join(filter(str.isdigit, trans_text))  
                    if trans_text not in ['0', ' ']:                            
                        if not any(item.get('트랜스지방', '') == trans_text for item in results['items']):        
                            results['items'].append({'트랜스지방': trans_text})
                            
            elif '포화' in text.description:
                vertices = text.bounding_poly.vertices
                next_vertex = texts[i+2].bounding_poly.vertices[0] 
                pohwa_text = texts[i+2].description
                if next_vertex.x > vertices[2].x: 

                    for check in ['(', ':']:
                        if check in pohwa_text:
                            pohwa_text = texts[i+2].description
                        pohwa_text = ''.join(filter(str.isdigit, pohwa_text))  
                    if pohwa_text not in ['0', ' ']:                            
                        if not any(item.get('포화지방', '') == pohwa_text for item in results['items']):        
                            results['items'].append({'포화지방': pohwa_text})
                            
            elif '지방' in text.description :
                vertices = text.bounding_poly.vertices
                next_vertex = texts[i+1].bounding_poly.vertices[0] 
                fat_text = texts[i+1].description
                if next_vertex.x > vertices[2].x: 

                    for check in ['(', ':']:
                        if check in fat_text: 
                            fat_text = texts[i+2].description 
                        fat_text = ''.join(filter(str.isdigit, fat_text))
                    if fat_text not in ['0', ' ']:
                        if fat_text not in [item.get('포화지방', '') for item in results['items']] and fat_text not in [item.get('트랜스지방', '') for item in results['items']]:
                            results['items'].append({'지방': fat_text}) 


        return Response(response=json.dumps(results), status=200, mimetype='application/json')

            # def extract_nutrients(texts):
        #     nutrients = {}
        #     detect_name = ['탄수화물', '단백질', '지방', '내용량']

        #     for i, text in enumerate(texts):
        #         for name in detect_name:
        #             if name in text.description:
        #                 vertices = text.bounding_poly.vertices
        #                 next_vertex = texts[i+1].bounding_poly.vertices[0]
        #                 nutrient_text = texts[i+1].description
        #                 if next_vertex.x > vertices[2].x:
        #                     for check in ['(', ':']:
        #                         if check in nutrient_text:
        #                             nutrient_text = texts[i+2].description
        #                 nutrients[name] = nutrient_text

        #     # JSON 형식으로 응답을 반환
        #     return {'result': 'success', 'nutrients': nutrients}, 200
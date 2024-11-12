from io import StringIO
import requests
import os
import struct
import comfy.utils
import time
import json
import subprocess
import sys
from PIL import Image, ExifTags
import numpy
import io



#将生成的结果文件上传至tos
class SaveImageOSS:
    @classmethod
    def INPUT_TYPES(s):
        return {"required":
                    {
                        "images": ("IMAGE", ),
                        "ak": ("STRING", ), # tos ak 
                        "sk": ("STRING", ), # tos sk
                        "tos_file_name": ("STRING", ), # tos对应文件目录
                        "endpoint": ("STRING", ), # tos endpoint
                        "region": ("STRING", ), # tos region
                        "bucket_name": ("STRING", ), # tos bucket_name
                        "order_no": ("STRING", ), # 标识
                        "call_back": ("STRING", ), # 回调地址
                        }
                }

    RETURN_TYPES = ()
    
    FUNCTION = "save_images"

    OUTPUT_NODE = True

    CATEGORY = "api/image"

    def save_images(self, ak, sk,images,tos_file_name,endpoint,region,bucket_name,order_no,call_back):
        import tos
        call_back_req={
            "status":1,
            "code":200,
            "message":"success",
            "data":[]
        }
        ak='AKLTNDBlOTdiMjQ2NDk5NDc2Zjk2OWMyZWI0YzcyYWQwNjU'
        sk='WVdJMlltSmhNMk0wTURabE5EVTBNRGs0WldJNFpUQXdaRGczWWpFMVl6Yw=='
        try:
            client = tos.TosClientV2(ak, sk, endpoint, region)
            
            idx = 0
            for image in images:
                array = 255. * image.cpu().numpy()
                img = Image.fromarray(numpy.clip(array, 0, 255).astype(numpy.uint8))

                # 创建一个字节流
                byte_io = io.BytesIO()
                # 将图像保存到字节流中，格式可以是 'PNG' 或 'JPEG'
                img.save(byte_io, format="png")
                # 重置字节流的位置
                byte_io.seek(0)

                
                client.put_object(bucket_name, f"{tos_file_name}/{idx}.png", content=byte_io.read())
                call_back_req['data'].append({"order_name":order_no,"image_name":f"{idx}.png","file_name":f"{tos_file_name}/{idx}.png"})
                idx = idx+1
        except Exception as e:
            print('fail with unknown error: {}'.format(e))
            call_back_req['status']=0
            call_back_req['code']=500
            call_back_req['message']=format(e)
            

        #TODO 回调通知接口
        # 认证
        header={
            "Authorization": "Bearer ",
            "Content-Type": "application/json",
            'X-DashScope-Async': 'enable'
        }
        requests.post(call_back,headers=header,data=json.dumps(call_back_req))
        
        return {}

    @classmethod
    def IS_CHANGED(s, images):
        return time.time()

    @classmethod
    def install_requirements(cls):
        requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
        if os.path.isfile(requirements_path):
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])

    def __init__(self):
        self.install_requirements()


NODE_CLASS_MAPPINGS = {
    "SaveImageOSS": SaveImageOSS,
}

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
                        "output_name": ("STRING",{"default": ""}),
                        "exten": (['png', 'jpg', 'jpeg', 'gif', 'tiff', 'webp', 'bmp'], ),
                        "ak": ("STRING", {"forceInput": True}), # tos ak 
                        "sk": ("STRING", {"forceInput": True}), # tos sk
                        "tos_file_name": ("STRING",  {"forceInput": True}), # tos对应文件目录
                        "endpoint": ("STRING", {"forceInput": True}), # tos endpoint
                        "region": ("STRING", {"forceInput": True}), # tos region
                        "bucket_name": ("STRING", {"forceInput": True}), # tos bucket_name
                        "order_no": ("STRING", {"forceInput": True}), # 标识
                        "order_id": ("STRING", {"forceInput": True}), # 标识
                        "call_back": ("STRING", {"forceInput": True}), # 回调地址
                        }
                }
    
    RETURN_TYPES = ()

    FUNCTION = "save_images"

    OUTPUT_NODE = True

    CATEGORY = "api/image"



    def save_images(self, ak, sk,images,tos_file_name,endpoint,region,bucket_name,order_no,order_id,call_back,output_name="",exten="png"):

        

        import tos
        call_back_req={
            "code":200,
            "message":"success",
            "orderNo":order_no,
            "orderId":order_id,
            "aiGenerateUrls":[]
        }
        try:
            client = tos.TosClientV2(ak, sk, endpoint, region)
            now = time.time()
            idx =  int(now * 1000)
            # 生成文件名
            if output_name=="":
                output_name = str(idx)
            
            file = f"lora_{output_name}.{exten}"
            for image in images:
                array = 255. * image.cpu().numpy()
                img = Image.fromarray(numpy.clip(array, 0, 255).astype(numpy.uint8))

                # 创建一个字节流
                byte_io = io.BytesIO()
                # 将图像保存到字节流中，格式可以是 'PNG' 或 'JPEG'
                img.save(byte_io, format=exten)
                # 重置字节流的位置
                byte_io.seek(0)

                file_name = f"{tos_file_name}/{file}"
                aiGenerateUrls = file_name
                client.put_object(bucket_name, file_name, content=byte_io.read())
                now1= int(time.time())
                print(f"oss_image_save,推送oos耗时,{(now1-now)*1000}s")
                call_back_req['aiGenerateUrls'].append(aiGenerateUrls)
        except Exception as e:
            print('fail with unknown error: {}'.format(e))
            call_back_req['code']=500
            call_back_req['message']=format(e)
            

        #TODO 回调通知接口
        # 认证
        header={
            "Authorization": "Bearer ",
            "Content-Type": "application/json",
            'X-DashScope-Async': 'enable'
        }
        print(f"oss_image_save:{call_back}")
        print(f"oss_image_save:{json.dumps(call_back_req)}")
        res=requests.post(call_back,headers=header,data=json.dumps(call_back_req))
        print(f"oss_image_save:{res.content}")
        now2= int(time.time())
        print(f"oss_image_save,接口耗时,{(now2-now1)*1000}s")
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

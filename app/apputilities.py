import requests 
       
extension_dict = {
    'image/png': '.png',
    'image/jpg': '.jpg',
    'image/jpeg': '.jpeg'
}
            
def check_img_url(img_url):
    allowed_headers = ["image/png", "image/jpg", "image/jpeg"]
    try:
        req_attempt = requests.head(img_url)
        req_header = req_attempt.headers["content-type"]
        if req_header in allowed_headers:
            return (True, req_header)
        else:
            return (False, None)
    except:
        return (False, None)


import urllib.request
import re

html = urllib.request.urlopen('https://deep-shield-pink.vercel.app/').read().decode('utf-8')
js_files = re.findall(r'src=\"(/assets/[^\"]+\.js)\"', html)

found = False
for js in js_files:
    js_url = 'https://deep-shield-pink.vercel.app' + js
    print('Checking', js_url)
    js_code = urllib.request.urlopen(js_url).read().decode('utf-8')
    if 'ar07xd-deepshield.hf.space' in js_code:
        print('FOUND Hugging Face URL in bundle!')
        found = True
    else:
        print('NOT FOUND in this bundle.')

if not found:
    print("\nCONCLUSION: The URL is NOT in the Vercel deployed code!")
else:
    print("\nCONCLUSION: The URL IS in the Vercel deployed code! The user needs to hard refresh.")

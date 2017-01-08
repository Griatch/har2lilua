-- LoadImpact user scenario script test.lua
-- converted by har2lilua 0.5 from test.har (created by WebInspector 537.36).

-- User-agent string based on request headers.

http.set_user_agent_string("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36")

-- Page http://localhost:8000/ (HAR pageref 'page_35')

http.page_start("page_35")

responses = http.request_batch({
    { "GET",
       "http://localhost:8000/",
       "127.0.0.1",
       {["Accept-Language"]="en-US,en;q=0.8", ["Accept-Encoding"]="gzip, deflate, sdch, br", ["If-Modified-Since"]="Thu, 05 Jan 2017 22:40:13 GMT", ["Connection"]="keep-alive", ["Accept"]="text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", ["User-Agent"]="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36", ["Host"]="localhost:8000", ["Cookie"]="Pycharm-9a9b8bf1=4d0aeb80-ccca-4424-9563-29821dcb0978; csrftoken=FZthdy1ortWAgnJPdWxzGu9no3t85NvM", ["Cache-Control"]="max-age=0", ["Upgrade-Insecure-Requests"]="1"},
       nil,
       nil, nil, 631, false, nil }
})

http.page_end("page_35")


-- Page http://localhost:8000/ (HAR pageref 'page_36')

http.page_start("page_36")

responses = http.request_batch({
    { "POST",
       "http://localhost:8000/",
       "127.0.0.1",
       {["Origin"]="http://localhost:8000", ["Content-Length"]="73", ["Accept-Language"]="en-US,en;q=0.8", ["Accept-Encoding"]="gzip, deflate, br", ["Connection"]="keep-alive", ["Accept"]="text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8", ["Upgrade-Insecure-Requests"]="1", ["Host"]="localhost:8000", ["Cookie"]="Pycharm-9a9b8bf1=4d0aeb80-ccca-4424-9563-29821dcb0978; csrftoken=FZthdy1ortWAgnJPdWxzGu9no3t85NvM", ["Cache-Control"]="max-age=0", ["Referer"]="http://localhost:8000/", ["User-Agent"]="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36", ["Content-Type"]="application/x-www-form-urlencoded"},
       [[text1=text+default&text2=a%CF%89b&binary=binary&a.html=a.html&a.txt=a.txt]],
       nil, nil, 217, false, nil }
})

http.page_end("page_36")


-- Sleep client
client.sleep(math.random(20, 40))

bili2.0  
1.本项目已经取代https://github.com/yjqiang/bilibili-live-tools  
2.项目初期只是想作为多用户分支，结果做完后发现，比原来项目做了很多。比如结构优化、很多函数调整、web_session独立以及一些新的功能等，而且对单用户也很友好  
3.旧项目理论上不再加入新功能，旧项目所有功能基本都已经在bili2.0中支持，但旧项目仍然会有一些必要的bug修复  








写下使用方法吧
Liunx 命令是pip3 和python3   windows 是pip和python
先下载项目到电脑https://github.com/yjqiang/bili2.0
安装python3.7，安装方法请自行百度
项目中有个requirements.txt 文件是要装的模块
执行pip install -r requirements.txt 安装模块
/conf/user.toml是用户目录在里面添加自己的账号
/conf/ctrl.toml是用户配置里面有说明按需要开启功能


获取用户登录信息
下载这个项目https://github.com/yjqiang/bilibili-live-tools
Python和需要模块都装好了直接运行python run.py
他会提示你输入用户名密码
输入完登录后就可以关了
在本项目/conf/ bilibili.toml 文件里面有你登录的信息复制到bili2.0的
/conf/user.toml里面就好了
 
然后进入bili2.0的文件夹里python run.py就能运行了

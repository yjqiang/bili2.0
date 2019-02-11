bili2.0  
========
1. 本项目已经取代https://github.com/yjqiang/bilibili-live-tools  
2. 项目初期只是想作为多用户分支，结果做完后发现，比原来项目做了很多。比如结构优化、很多函数调整、web_session独立以及一些新的功能等，而且对单用户也很友好  
3. 旧项目理论上不再加入新功能，旧项目所有功能基本都已经在bili2.0中支持，但旧项目仍然会有一些必要的bug修复  


使用方法
========
1. 先下载项目到电脑https://github.com/yjqiang/bili2.0/archive/master.zip
2. 安装python3.6+，安装方法请自行谷歌/百度
3. [requirements.txt](https://github.com/yjqiang/bili2.0/blob/master/requirements.txt)是所需第三方模块，执行`pip install -r requirements.txt`安装模块
4. [/conf/user.toml](https://github.com/yjqiang/bili2.0/blob/master/conf/user.toml)是用户目录，在里面添加自己的账号；[/conf/ctrl.toml](https://github.com/yjqiang/bili2.0/blob/master/conf/ctrl.toml)是用户配置，里面有说明按需要开启功能
5. Python和需要模块都装好了直接运行`python run.py`

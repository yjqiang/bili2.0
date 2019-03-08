bili2.0  
========
1. 本项目已经取代https://github.com/yjqiang/bilibili-live-tools  
2. 项目初期只是想作为多用户分支，结果做完后发现，比原来项目做了很多。比如结构优化、很多函数调整、web_session独立以及一些新的功能等，而且对单用户也很友好  
3. 旧项目理论上不再加入新功能，旧项目所有功能基本都已经在bili2.0中支持，但旧项目仍然会有一些必要的bug修复  


使用方法
-------
1. 先下载项目到电脑https://github.com/yjqiang/bili2.0/archive/master.zip
2. 安装python3.6+，安装方法请自行谷歌/百度
3. [requirements.txt](https://github.com/yjqiang/bili2.0/blob/master/requirements.txt)是所需第三方模块，执行`pip install -r requirements.txt`安装模块
4. [/conf/user.toml](https://github.com/yjqiang/bili2.0/blob/master/conf/user.toml)是用户目录，在里面添加自己的账号；[/conf/ctrl.toml](https://github.com/yjqiang/bili2.0/blob/master/conf/ctrl.toml)是用户配置，里面有说明按需要开启功能
5. Python和需要模块都装好了直接运行`python run.py`

使用`Docker`快速使用方法 (每次启动的时候都会通过git pull同步主项目代码。)
-------
1. 安装好[Docker](https://yeasy.gitbooks.io/docker_practice/content/install/)
2. 如果你需要对应的功能，就下载对应的功能文件。参照看上面的`使用方法`。
  - [/conf/user.toml（添加用户，必下）](https://raw.githubusercontent.com/yjqiang/bili2.0/master/conf/user.toml)
  - [/conf/ctrl.toml 用户配置文件（如果不需要修改，不用下）](https://raw.githubusercontent.com/yjqiang/bili2.0/master/conf/ctrl.toml)
  - [run.py 动态抽奖开关 （如果不需要修改，不用下）](https://raw.githubusercontent.com/yjqiang/bili2.0/master/run.py)
3. 在本地修改好文件。
4. docker镜像启动时，把文件挂载到镜像即可。

```
docker run --rm -it \
  -v $(pwd)/user.toml:/app/conf/user.toml \
  -v $(pwd)/ctrl.toml:/app/conf/ctrl.toml \
  -v $(pwd)/run.py:/app/run.py \
  zsnmwy/bili2.0
```

`$(pwd)` 获取当前目录路径。

`--rm` 退出的时候，会把容器删除。

`-i` 让容器的标准输入保持打开。

`-t` 让Docker分配一个伪终端（pseudo-tty）并绑定到容器的标准输入上。

`-d `让容器后台运行。如果你想后台，加个在`-it`后面加个`d`就行。

`-v` 可以把本机的(目录/文件)挂载到容器里面，起到替换的作用。如果你使用的是项目的默认值，则不用-v来指定文件替换。但是用户文件（`user.toml`）是一定要替换的，不然程序找不到用户的。

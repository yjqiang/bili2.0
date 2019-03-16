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
4. [/conf/user.sample.toml](https://github.com/yjqiang/bili2.0/blob/master/conf/user.sample.toml)是用户目录示例，在里面添加自己的账号；[/conf/ctrl.sample.toml](https://github.com/yjqiang/bili2.0/blob/master/conf/ctrl.sample.toml)是用户配置示例，里面有说明按需要开启功能。需要自己定制这两个文件（不是在原来sample文件上改，而是自己在conf文件夹内新建user.toml和ctrl.toml文件，在新文件上面改（注意全部复制过去后再改，sample文件只作为用户使用参考，程序运行不会读取此文件，只会读取用户的新建toml文件））
5. Python和需要模块都装好了直接运行`python run.py`
6. 节奏风暴默认关闭，开启需要[monitor_danmu.py](https://github.com/yjqiang/bili2.0/blob/master/monitor_danmu.py#L82) 和 [monitor_danmu.py](https://github.com/yjqiang/bili2.0/blob/master/monitor_danmu.py#L182) 取消注释，抢风暴的逻辑可以自由定制 [/tasks/storm_raffle_handler.py](https://github.com/yjqiang/bili2.0/blob/master/tasks/storm_raffle_handler.py)
7. 动态抽奖开关在[run.py](https://github.com/yjqiang/bili2.0/blob/master/run.py#L96) ，需要在[/conf/ctrl.toml](https://github.com/yjqiang/bili2.0/blob/master/conf/ctrl.toml)更新`dyn_lottery_friends`，参与的抽奖会在dyn里面产生一个database数据库（sqlite3）。**注意：在[数据库格式更新的commit](https://github.com/yjqiang/bili2.0/commit/93fb545add5e3e51adc4704f51def3a5468d8e4a)前运行过动态抽奖的用户请先运行[add_colomn_joined2old_staus_table.py](https://github.com/yjqiang/bili2.0/blob/master/dyn/add_colomn_joined2old_staus_table.py)升级数据库。**


使用`Docker`快速使用方法 (每次启动的时候都会通过`git pull`同步主项目代码。)
-------
1. 安装好[Docker](https://yeasy.gitbooks.io/docker_practice/content/install/)
2. 如果你需要对应的功能，就下载对应的功能文件。参照看上面的`使用方法`。
  - [/conf/user.sample.toml（添加用户，必下）](https://raw.githubusercontent.com/yjqiang/bili2.0/master/conf/user.sample.toml)
  - [/conf/ctrl.sample.toml 用户配置文件（如果不需要修改，不用下）](https://raw.githubusercontent.com/yjqiang/bili2.0/master/conf/ctrl.sample.toml)
  - [run.py 动态抽奖开关 （如果不需要修改，不用下）](https://raw.githubusercontent.com/yjqiang/bili2.0/master/run.py)
3. 在本地修改好文件。
4. docker镜像启动时，把文件挂载到容器即可。

---

### Linux

```
docker run --rm -it \
  -v $(pwd)/user.sample.toml:/app/conf/user.toml \
  -v $(pwd)/ctrl.sample.toml:/app/conf/ctrl.toml \
  -v $(pwd)/run.py:/app/run.py \
  zsnmwy/bili2.0
```

`$(pwd)` 获取当前目录路径。

### Windows

假设下载的文件都在`D:\python`。

```
下面命令需要在powershell上面执行。

docker run --rm -it `
  -v D:\python\user.sample.toml:/app/conf/user.toml `
  -v D:\python\ctrl.sample.toml:/app/conf/ctrl.toml `
  -v D:\python\run.py:/app/run.py `
  zsnmwy/bili2.0
```
---

下面的指令都是docker本身的指令，适用于`Windows`以及`Linux`。

`--rm` 退出的时候，会把容器删除。

`-i` 让容器的标准输入保持打开。

`-t` 让Docker分配一个伪终端（pseudo-tty）并绑定到容器的标准输入上。

`-d `让容器后台运行。如果你想后台，加个在`-it`后面加个`d`就行。

`-v` 可以把本机的(目录/文件)挂载到容器里面，起到加入/替换的作用。如果你使用的是项目的默认值，则不用-v来指定文件替换。但是用户文件（`user.toml`）是一定要的，不然程序找不到用户的。

---

如果有什么奇葩问题，或者需要更新镜像，使用`docker pull zsnmwy/bili2.0`进行更新。

### 已知问题

在`-it`交互模式下，在容器运行着的python直接用`Ctrl+C`无法正常退出容器。

需要使用`docker rm -f`强制结束。

```
$docker ps
CONTAINER ID        IMAGE               COMMAND                  CREATED             STATUS              PORTS               NAMES
a746fb0325fb        zsnmwy/bili2.0      "/bin/sh -c 'git pul…"   44 seconds ago      Up 42 seconds                           frosty_mccarthy

$docker rm -f a7
a7
```

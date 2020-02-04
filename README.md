# bili2.0  

1. 本项目已经取代 <https://github.com/yjqiang/bilibili-live-tools>，旧项目已经***完全废除***，不再提供更新和 bug 修复
1. 项目初期只是想作为多用户分支，结果做完后发现，比原来项目做了很多。比如结构优化、很多函数调整、web_session 独立以及一些新的功能等，而且对单用户也很友好
1. [WIKI](https://github.com/yjqiang/bili2.0/wiki) 里面有一些功能说明，以及代码一些设计细节

### 特别感谢

1. <https://github.com/lzghzr/bilive_client> 该项目作者的大力支持
2. [Coderx for GitHub](https://apps.apple.com/app/apple-store/id1371929193) 的作者 <https://github.com/CoderxforGitHub> 对用户任务设计等的帮助以及其开发的 Github 软件的便利

### 支持与打赏
![](support.jpeg)

### 使用方法

1. 先下载项目到电脑 <https://github.com/yjqiang/bili2.0/archive/master.zip>
1. 安装 python3.6+，安装方法请自行谷歌/百度
1. [requirements.txt](requirements.txt) 是所需第三方模块，执行 `pip install -r requirements.txt` 安装模块
1. [/conf/user.sample.toml](conf/user.sample.toml) 是用户目录示例，在里面添加自己的账号；[/conf/ctrl.sample.toml](conf/ctrl.sample.toml) 是用户配置示例，里面有说明按需要开启功能；
[/conf/task.sample.toml](conf/task.sample.toml) 是任务（小电视、勋章投喂等）控制。需要自己定制这几个文件（不是在原来 sample 文件上改，而是自己在 conf 文件夹内新建 user.toml、ctrl.toml 和 task.toml 文件，在新文件上面改（注意全部复制过去后再改，sample 文件只作为用户使用参考，程序运行不会读取此文件，只会读取用户的新建 toml 文件））
1. Python 和需要模块都装好了直接 **cmd** 运行 `python run.py`
1. 节奏风暴默认关闭，开启需要把 [/conf/task.sample.toml](conf/task.sample.toml) 的 `join_storm_raffle`  修改，抢风暴的逻辑可以自由定制 [/tasks/storm_raffle_handler.py](tasks/storm_raffle_handler.py)
1. 动态和实物抽奖总开关（这里的开关是程序暴力轮询总开关，与 [/conf/task.sample.toml](conf/task.sample.toml) 中的不一样，task控制的是单个用户是否参与）在 [ctrl.sample.toml](conf/ctrl.sample.toml) ，开启后需要在 [/conf/task.sample.toml](conf/task.sample.toml) 更新 `dyn_lottery_friends`（这是转发动态艾特的人选），参与的抽奖会在 dyn 里面产生一个 database 数据库(sqlite3)。

### 使用 Docker 快速使用方法 (每次启动的时候都会通过 `git pull` 同步主项目代码)

1. 安装好 [Docker](https://yeasy.gitbooks.io/docker_practice/content/install/)
2. 如果你需要对应的功能，就下载对应的功能文件。参照看上面的[使用方法](#使用方法)。
3. 在本地修改好文件。
4. Docker 镜像启动时，把文件挂载到容器即可。

##### Docker in Linux

```
docker run --rm -it \
  -v $(pwd)/user.sample.toml:/app/conf/user.toml \
  -v $(pwd)/ctrl.sample.toml:/app/conf/ctrl.toml \
  -v $(pwd)/task.sample.toml:/app/conf/task.toml \
  zsnmwy/bili2.0
```

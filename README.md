bili3.0主要更新（比较2.0）  
1.对tasks和reqs均做了区分，不同的任务种类做不一样的事情。比如`tv_raffle_handler`，顾名思义，这个class里面就是处理小电视的东西  
2.tasks和reqs由原来的user成员函数变成了独立的各个静态函数，用户行为与用户尽量分离，同时减小了user这个实例对大小    
3.tasks的入口以及上下任务的连接设计。这里的task分两类，一种是真正的task，比如`tv_raffle_handler`，check->join->notify，构成了task执行链条，执行的下一个链条通过return的返回值控制，在notifier.py里的`__exec_one_step`具体执行，可以broadcast；另一种不是task，只是普通的函数，执行一次就够了，例如utils.py这些  
4.针对403问题，在web_session.py里面加了一个全局锁`sem = asyncio.Semaphore(3)`，控制流量大小，目前基本完全杜绝了403（晚高峰测试50用户,其中包括了节奏风暴暴力*2）。值得注意的是，如果数值过小比如1，那么就相当于一个单流量的了，那么延迟可能很高，你设置了3分钟后执行`tv_raffle_handler.join`，session可能5分钟后才排到队，发出网络请求；如果数值过高，那么可能就403了  
5.bili_cobsole对数据输入办法进行了控制，需要输入“指令序号+详细控制”一次性全部输入，例如“1 -u 0”，表示对用户0执行1号命令，具体什么控制这里可以看代码，一般用u表示用户index，p表示房间号码，n表示数量。默认的u是0  


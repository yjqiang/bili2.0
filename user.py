from daily_job_user import DailyJobUser
from join_raffle_user import JoinRaffleUser
from login_user import LoginUser
from web_hub import WebHub, HostWebHub
from states import UserStates
from statistic import Statistics


class User(DailyJobUser, JoinRaffleUser, LoginUser):
    def __init__(self, user_id, dict_user, dict_bili, task_control, high_concurency):
        if high_concurency:
            self.webhub = HostWebHub(user_id, dict_user, dict_bili)
        else:
            self.webhub = WebHub(user_id, dict_user, dict_bili)
        self.statistics = Statistics()
        self.user_id = user_id
        self.user_name = dict_user['username']
        self.user_password = dict_user['password']
        self.task_control = task_control
        self.state = UserStates(user_id, self.user_name)
        self.handle_login_status()
            


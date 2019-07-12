from os import path
import toml


# "#969696"
def hex_to_rgb_percent(str_hex):
    return int(str_hex[1:3], 16)/255, \
           int(str_hex[3:5], 16)/255, \
           int(str_hex[5:7], 16)/255


# [255 255 255]
def dec_to_rgb_percent(list_rgb):
    return list_rgb[0]/255, list_rgb[1]/255, list_rgb[2]/255
    
    
class ConfLoader:
    def __init__(self):
        path_conf = f'{path.dirname(path.realpath(__file__))}/conf'
        self.file_color = f'{path_conf}/color.toml'
        self.file_user = f'{path_conf}/user.toml'
        self.file_bili = f'{path_conf}/bili.toml'
        self.file_ctrl = f'{path_conf}/ctrl.toml'
        self.file_task = f'{path_conf}/task.toml'
        
        '''
        self.dict_color = self.read_color()
        print(self.dict_color)
        
        self.dict_user = self.read_user()
        print(self.dict_user)
        
        self.dict_bili = self.read_bili()
        print(self.dict_bili)
        print("# 初始化完成")
        '''
        
    @staticmethod
    def toml_load(path):
        with open(path, encoding="utf-8") as f:
            return toml.load(f)
    
    @staticmethod
    def toml_dump(object, path):
        with open(path, 'w', encoding="utf-8") as f:
            toml.dump(object, f)
    
    def write_user(self, dict_new, user_id):
        dict_user = self.toml_load(self.file_user)
        for i, value in dict_new.items():
            dict_user['users'][user_id][i] = value
        self.toml_dump(dict_user, self.file_user)
            
    def read_bili(self):
        return self.toml_load(self.file_bili)
        
    def read_color(self):
        dict_color = self.toml_load(self.file_color)
        for i in dict_color.values():
            for key, color in i.items():
                if isinstance(color, str):
                    i[key] = hex_to_rgb_percent(color)
                elif isinstance(color, list):
                    i[key] = dec_to_rgb_percent(color)
                        
        return dict_color
     
    def read_user(self):
        return self.toml_load(self.file_user)
        
    def read_ctrl(self):
        return self.toml_load(self.file_ctrl)

    def read_task(self):
        return self.toml_load(self.file_task)
        
                
var = ConfLoader()


def write_user(dict_new, user_id):
    var.write_user(dict_new, user_id)

        
def read_bili():
    return var.read_bili()
    
            
def read_color():
    return var.read_color()

      
def read_user():
    return var.read_user()

        
def read_ctrl():
    return var.read_ctrl()


def read_task():
    return var.read_task()

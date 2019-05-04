from os import path
import toml


# "#969696"
def hex_to_rgb_percent(str_hex):
    return tuple(int(n, 16)/255 for n in (str_hex[1:3], str_hex[3:5], str_hex[5:7]))


# [255 255 255]
def rgb_to_percent(list_rgb):
    return list_rgb[0]/255, list_rgb[1]/255, list_rgb[2]/255
    
    
class ConfLoader:
    def __init__(self):
        path_conf = f'{path.dirname(path.realpath(__file__))}/conf'
        self.file_color = f'{path_conf}/color.toml'
        self.file_user = f'{path_conf}/user.toml'
        self.file_bili = f'{path_conf}/bili.toml'
        self.file_ctrl = f'{path_conf}/ctrl.toml'
        
        '''
        self.dict_color = self.read_color()
        print(self.dict_color)
        
        self.dict_user = self.read_user()
        print(self.dict_user)
        
        self.dict_bili = self.read_bili()
        print(self.dict_bili)
        print("# 初始化完成")
        '''
    
    def write_user(self, dict_new, user_id):
        with open(self.file_user, encoding="utf-8") as f:
            dict_user = toml.load(f)
        for i, value in dict_new.items():
            dict_user['users'][user_id][i] = value
        with open(self.file_user, 'w', encoding="utf-8") as f:
            toml.dump(dict_user, f)
            
    def read_bili(self):
        with open(self.file_bili, encoding="utf-8") as f:
            dict_bili = toml.load(f)
        return dict_bili
        
    def read_color(self):
        with open(self.file_color, encoding="utf-8") as f:
            dict_color = toml.load(f)
        for i in dict_color.values():
            for key, color in i.items():
                if isinstance(color, str):
                    i[key] = hex_to_rgb_percent(color)
                elif isinstance(color, list):
                    i[key] = rgb_to_percent(color)
                        
        return dict_color
     
    def read_user(self):
        with open(self.file_user, encoding="utf-8") as f:
            dict_user = toml.load(f)
        return dict_user
        
    def read_ctrl(self):
        with open(self.file_ctrl, encoding="utf-8") as f:
            dict_ctrl = toml.load(f)
        return dict_ctrl
        
                
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

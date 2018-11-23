import toml


# "#969696"
def hex_to_rgb_percent(hex_str):
    return tuple(int(n, 16)/255 for n in (hex_str[1:3], hex_str[3:5], hex_str[5:7]))


# [255 255 255]
def rgb_to_percent(rgb_list):
    return rgb_list[0]/255, rgb_list[1]/255, rgb_list[2]/255
    
    
class ConfigLoader():
    
    inst = None

    def __new__(cls, file_color=None, file_user=None, file_bili=None, file_ip=None):
        if not cls.inst:
            cls.inst = super(ConfigLoader, cls).__new__(cls)
            cls.inst.file_color = file_color
            # cls.inst.dict_color = cls.inst.read_color()
            # print(cls.inst.dict_color)
            
            cls.inst.file_user = file_user
            # cls.inst.dict_user = cls.inst.read_user()
            # print(cls.inst.dict_user)
            
            cls.inst.file_bili = file_bili
            # cls.inst.dict_bili = cls.inst.read_bili()
            # print(cls.inst.dict_bili)
            # print("# 初始化完成")
            
            cls.inst.file_ip = file_ip
            # cls.inst.dict_ip = cls.inst.read_ip()
            # print(cls.inst.dict_ip)
        return cls.inst
    
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
        
    def read_ip(self):
        with open(self.file_ip, encoding="utf-8") as f:
            dict_ip = toml.load(f)
        return dict_ip
        
    def read_color(self):
        with open(self.file_color, encoding="utf-8") as f:
            dict_color = toml.load(f)
        for i in dict_color.values():
            for j in i.keys():
                if isinstance(i[j], str):
                    i[j] = hex_to_rgb_percent(i[j])
                else:
                    i[j] = rgb_to_percent(i[j])
                        
        return dict_color
     
    def read_user(self):
        with open(self.file_user, encoding="utf-8") as f:
            dict_user = toml.load(f)
        return dict_user
        
        
        


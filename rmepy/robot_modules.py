from . import logger
from .decorators import accepts

class RobotModuleTemplate(object):
    def __init__(self, robot):
        self.send_cmd = robot.send_cmd
        self.send_query = robot.send_query
        self.log = logger.Logger('Commends')

    def _process_response(self, data, type_list):
        try:
            data = data.split(' ')
            if type(type_list) == list:
                data = [f(i) if f != bool else bool(int(i))
                        for i, f in zip(data, type_list)]
            else:
                data = [type_list(i) if type_list != bool else bool(int(i))
                        for i in data]
        except (TypeError, ValueError) as e:
            self.log.error(
                "Error at processing response: %s does not match %s" % (data, type_list))
            data = None
        return data


class BasicCtrl(RobotModuleTemplate):
    def __init__(self, robot):
        super().__init__(robot)

    def enter_sdk_mode(self):
        """控制机器人进入 SDK 模式

        当机器人成功进入 SDK 模式后，才可以响应其余控制命令

        Args:
            None

        Returns:
            None

        """
        return self.send_cmd('commend')

    def quit_cmd_mode(self):
        """退出 SDK 模式

        控制机器人退出 SDK 模式，重置所有设置项
        Wi-Fi/USB 连接模式下，当连接断开时，机器人会自动退出 SDK 模式

        Args:
            None

        Returns:
            None

        """
        return self.send_cmd('quit')

    @accepts((int, 0, 2))
    def set_robot_mode(self, mode):
        """设置机器人的运动模式

        机器人运动模式描述了云台与底盘之前相互作用与相互运动的关系，
        每种机器人模式都对应了特定的作用关系。

        Args:
            mode (enum): 机器人运动模式
                {0:云台跟随底盘模式, 1:底盘跟随云台模式, 2:自由模式}

        Returns:
            None

        """
        mode_enum = ('chassis_lead', 'gimbal_lead', 'free')
        # if mode not in (0, 1, 2):
        #     self.log.error(
        #         "Set_chassis_following_mode: 'mode' must be an integer from 0 to 2")
        return self.send_cmd('robot mode ' + mode_enum[mode])

    def get_robot_mode(self):
        """获取机器人运动模式

        查询当前机器人运动模式
        机器人运动模式描述了云台与底盘之前相互作用与相互运动的关系，
        每种机器人模式都对应了特定的作用关系。

        Args:
            None

        Returns:
            (int): 机器人的运动模式
                {0:云台跟随底盘模式, 1:底盘跟随云台模式, 2:自由模式}

        """
        mode_enum = ('chassis_lead', 'gimbal_lead', 'free')
        return mode_enum.index(self.send_cmd('robot mode ?'))

    def video_stream_on(self):
        """开启视频流推送

        打开视频流
        打开后，可从视频流端口接收到 H.264 编码的码流数据

        Args:
            None

        Returns:
            None

        """
        return self.send_cmd('stream on')

    def video_stream_off(self):
        """关闭视频流推送

        关闭视频流
        关闭视频流后，H.264 编码的码流数据将会停止输出

        Args:
            None

        Returns:
            None

        """
        return self.send_cmd('stream off')


class Chassis(RobotModuleTemplate):
    def __init__(self, robot):
        super().__init__(robot)

        # position 底盘当前的位置距离上电时刻位置
        self.x = 0.0  # x 轴位置(m)
        self.y = 0.0  # y 轴位置(m)
        self.z = 0.0  # 偏航角度(°)

        # attitude
        self.pitch = 0.0
        self.roll = 0.0
        self.yaw = 0.0

        # status
        self.is_static = False  #是否静止
        self.is_uphill = False  #是否上坡
        self.is_downhill  = False  #是否下坡
        self.is_on_slope = False  #是否溜坡
        self.is_pick_up  = False  #是否被拿起
        self.is_slip  = False  #是否滑行
        self.is_impact_x  = False  #x 轴是否感应到撞击
        self.is_impact_y = False  #y 轴是否感应到撞击
        self.is_impact_z = False  #z 轴是否感应到撞击
        self.is_roll_over = False  #是否翻车
        self.is_hill_static = False #是否在坡上静止

    @accepts(speed_x=(float, -3.5, 3.5), speed_y=(float, -3.5, 3.5), speed_yaw=(float, -600, 600))
    def set_vel(self, speed_x, speed_y, speed_yaw):
        """底盘运动速度控制

        控制底盘运动速度

        Args:
            speed_x (float:[-3.5,3.5]): x 轴向运动速度，单位 m/s
            speed_y (float:[-3.5,3.5]): y 轴向运动速度，单位 m/s
            speed_yaw (float:[-600,600]): z 轴向旋转速度，单位 °/s

        Returns:
            None

        """
        return self.send_cmd('chassis speed x %f y %f z %f' % (speed_x, speed_y, speed_yaw))

    @accepts((int, -1000, 1000), (int, -1000, 1000), (int, -1000, 1000), (int, -1000, 1000))
    def set_wheel_speed(self, speed_w1, speed_w2, speed_w3, speed_w4):
        """底盘轮子速度控制

        控制四个轮子的速度

        Args:
            speed_w1 (int:[-1000, 1000]): 右前麦轮速度，单位 rpm
            speed_w2 (int:[-1000, 1000]): 左前麦轮速度，单位 rpm
            speed_w3 (int:[-1000, 1000]): 右后麦轮速度，单位 rpm
            speed_w4 (int:[-1000, 1000]): 左后麦轮速度，单位 rpm

        Returns:
            None

        """
        return self.send_cmd('chassis wheel w1 %d w2 %d w3 %d w4 %d' % (speed_w1, speed_w2, speed_w3, speed_w4))

    @accepts((float, -5, 5), (float, -5, 5), (int, -1800, 1800), (float, 0, 3.5), (float, 0, 600))
    def shift(self, x=0., y=0., yaw=0, speed_xy=0.5, speed_yaw=90.):
        """底盘相对位置控制

        控制底盘运动当指定位置，坐标轴原点为当前位置

        Args:
            x  (float:[-5, 5]): x 轴向运动距离，单位 m
            y  (float:[-5, 5]): y 轴向运动距离，单位 m
            yaw  (int:[-1800, 1800]): z 轴向旋转角度，单位 °
            speed_xy  (float:(0, 3.5]): xy 轴向运动速度，单位 m/s
            speed_yaw  (float:(0, 600]): z 轴向旋转速度， 单位 °/s

        Returns:
            None

        """
        return self.send_cmd('chassis move x %f y %f z %d vxy %f vz %f' % (x, y, yaw, speed_xy, speed_yaw))

    def get_all_speed(self):
        """底盘速度信息获取

        获取底盘的速度信息

        Args:
            None

        Returns:
            (list) [
                speed_x (float): x轴向的运动速度，单位 m/s 
                speed_y (float): y轴向的运动速度，单位 m/s
                speed_yaw (float): z轴向的旋转速度，单位 °/s
                speed_w1 (int): 右前麦轮速度，单位 rpm
                speed_w2 (int): 左前麦轮速度，单位 rpm
                speed_w3 (int): 右后麦轮速度，单位 rpm
                speed_w4 (int): 左后麦轮速度，单位 rpm
                ]


        """
        response = self.send_query('chassis position ?')
        return self._process_response(response, (float, float, float, int, int, int, int))

    def get_speed(self):
        """获取机器人运动速度

        获取机器人整体的速度信息

        Args:
            None

        Returns:
            (list) [
                speed_x (float): x轴向的运动速度，单位 m/s 
                speed_y (float): y轴向的运动速度，单位 m/s
                speed_yaw (float): z轴向的旋转速度，单位 °/s
                ]

        """
        return self.get_all_speed(self)[:3]

    def get_wheel_speed(self):
        """获取麦轮速度

        获取麦轮的速度信息

        Args:
            None

        Returns:
            (list) [
                speed_w1 (int): 右前麦轮速度，单位 rpm
                speed_w2 (int): 左前麦轮速度，单位 rpm
                speed_w3 (int): 右后麦轮速度，单位 rpm
                speed_w4 (int): 左后麦轮速度，单位 rpm
                ]

        """
        return self.get_all_speed(self)[3:]

    def get_postion(self):
        """底盘位置信息获取

        获取底盘的位置信息
        上电时刻机器人所在的位置为坐标原点

        Args:
            None

        Returns:
            (list) [
                x (float): x轴向的位移
                y (float): y轴向的位移
                z (float): z轴向的位移
            ]

        """
        response = self.send_query('chassis position ?')
        return self._process_response(response, float)

    def get_attitude(self):
        """获取底盘姿态信息

        查询底盘的姿态信息

        Args:
            None

        Returns:   #TODO:确定返回值为 int 还是 float
            (list) [
                pitch (float): pitch 轴角度，单位 °
                roll (float): roll 轴角度，单位 °
                yaw (float): yaw 轴角度，单位 °
            ]

        """
        response = self.send_query('chassis attitude ?')
        return self._process_response(response, float)

    def get_status(self):
        """获取底盘状态信息

        获取底盘状态信息

        Args:
            None

        Returns:
            (list) [
                static (bool): 是否静止
                uphill (bool): 是否上坡
                downhill (bool): 是否下坡
                on_slope (bool): 是否溜坡
                pick_up (bool): 是否被拿起
                slip (bool): 是否滑行
                impact_x (bool): x 轴是否感应到撞击
                impact_y (bool): y 轴是否感应到撞击
                impact_z (bool): z 轴是否感应到撞击
                roll_over (bool): 是否翻车
                hill_static (bool): 是否在坡上静止
            ]

        """
        response = self.send_query('chassis status ?')
        return self._process_response(response, bool)

    # TODO: set_push_freq & data

class Gimbal(RobotModuleTemplate):
    def __init__(self, robot):
        super().__init__(robot)

        # attitude
        self.pitch = 0.0
        self.yaw = 0.0

    @accepts((float, -450, 450), (float, -450, 450))
    def set_speed(self, speed_pitch, speed_yaw):
        """云台运动速度控制
        
        控制云台运动速度
        
        Args:
            speed_pitch (float:[-450, 450]): pitch 轴速度，单位 °/s
            speed_yaw (float:[-450, 450]): yaw 轴速度，单位 °/s
        
        Returns:
            None
        
        """
        return self.send_cmd('gimbal speed p %s y %s' %(speed_pitch, speed_yaw))
    
    @accepts((float, -55, 55), (float, -55, 55), (float, 0, 540), (float, 0, 540))
    def shift(self, pitch=0., yaw=0., speed_pitch=30., speed_yaw=30.):
        """云台相对位置控制
        
        控制云台运动到指定位置，坐标轴原点为当前位置
        
        Args:
            pitch  (float:[-55, 55]): pitch 轴角度， 单位 °
            yaw  (float:[-55, 55]): yaw 轴角度，单位 °
            speed_pitch  (float:[0, 540]): pitch 轴运动速速，单位 °/s
            speed_yaw  (float:[0, 540]): yaw 轴运动速度，单位 °/s
        
        Returns:
            None
        
        """
        return self.send_cmd('gimbal move p %s y %s vp %s vy %s' %(pitch, yaw, speed_pitch, speed_yaw))
    
    @accepts((int, -25, 30), (int, -250, 250), (int, 0, 540), (int, 0, 540))
    def move_to(self, pitch, yaw, speed_pitch, speed_yaw):
        """云台绝对位置控制
        
        控制云台运动到指定位置，坐标轴原点为上电位置
        
        Args:
            pitch  (int:[-25, 30]): pitch 轴角度(°)
            yaw  (int:[-250, 250]): yaw 轴角度(°)
            speed_pitch  (int:[0, 540]): pitch 轴运动速度(°/s)
            speed_yaw  (int:[0, 540]): yaw 轴运动速度(°/s) # TODO 确认是 int 还是 float
        
        Returns:
            None
        
        """
        return self.send_cmd('gimbal moveto p %s y %s vp %s vy %s' %(pitch, yaw, speed_pitch, speed_yaw))
    
    def suspend(self):
        """云台休眠控制
        
        控制云台进入休眠状态
        
        Args:
            None
        
        Returns:
            None
        
        """
        return self.send_cmd('gimbal suspend')

    def resume(self):
        """云台恢复控制
        
        控制云台从休眠状态中恢复
        
        Args:
            None
        
        Returns:
            None
        
        """
        return self.send_cmd('gimbal resume')

    def recenter(self):
        """云台回中控制
        
        控制云台回中
        
        Args:
            None
        
        Returns:
            None
        
        """
        return self.send_cmd('gimbal recenter')

    def get_attitude(self):
        """云台姿态获取
        
        获取云台姿态信息
        
        Args:
            None
        
        Returns:
            (list) [
                pitch (int): pitch 轴角度(°)
                yaw (int): yaw 轴角度(°)
            ]
        
        """
        response = self.send_query('gimbal attitude ?')
        return self._process_response(response, int)
    
    # TODO push msg ctrl
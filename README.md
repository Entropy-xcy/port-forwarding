# YHJM2 ---- 移花接木

在转发过程中我们主要需要考虑三台机器，在下文中我们遵循以下定义：
* Server: 带有公网IP的公网服务器，用于提供公网IP转发的IP地址。
* Client: 带有内网IP的内网转发机，专门用于运行转发的中专服务。
* Host: 内网需要被转发的服务器，通常是这三台机器中配置最高的。

**目标： 将Server上的IP地址移花接木到Host机器上。从而让高配置的内网服务器拥有了公网IP地址。**
## 方法1：全自动安装（适用于Client端和Server端均为全新安装的Ubuntu2004操作系统的情况，并且用户已经拥有了无密码执行sudo指令的权限）
查看自动部署脚本细则：
```
python3 auto-deploy.py --help
```
**注：auto-deploy脚本需要在可以同时访问到Server和Client的SSH端口的机器上执行**

部署案例：
```
python3 auto-deploy.py --server_ip 8.8.8.8 --server_user root --server_pwd fuck_google --server_if eth0 --client_ip 10.0.0.1 --client_user myself --client_pwd passwordformyself --host_ip 10.0.0.2 --max_port 1000
```
## 方法2：手动安装（适用于非全新安装的Client端系统和Host端系统）
### 安装依赖
在Server端和Client端分别执行：
```
bash dep.sh
```
### 修改Client端和Server端SSH端口到52222
在Server端执行：
```
bash change-ssh-port.sh
```
请注意！！该脚本会将Server机的ssh端口改变到52222从而防止和穿透端口冲突。该脚本仅保证在Ubuntu2004默认ssh配置文件上可用。

### 常量申明
```
SERVER_IP=<server-ip>
CLIENT_IP=<client-ip>
HOST_IP=<host-ip>
MAX_PORT=<max_port>
SERVER_IF=<server-nic-name>
```
将以上变量定义进行如下替换：
* `<server-ip>`: Server端公网IP
* `<client-ip>`: Client端内网IP
* `<host-ip>`: 要被转发的机器的内网IP
* `<max_port>`: 最大进行转发的端口（转发端口的范围是`1:<max_port>`）
* `<server-nic-name>`: Server端拥有公网IP的网卡名称（例如`eth0`, `ens160`）

### 创建Wiregaurd Overlay网络
1. 在Server端执行：
```
bash wg-server.sh
```
这一步会输出一串key，我们将它称为server-pub-key。

2. 在Client端执行：
```
bash wg-client.sh
```
这一步会输出client-pub-key。

3. 在Server端与Client端建立链接，在Server端执行：
```
sudo wg set wg0 peer <client-pub-key> allowed-ips 10.0.5.0/24
```
4. 在Client端与Server端建立链接，在Client端执行：
```
sudo wg set wg0 peer <server-pub-key> allowed-ips 10.0.5.0/24 endpoint $SERVER_IP:52180 persistent-keepalive 1
```
5. 测试Wireguard Overlay网络的通讯，在Server端和Client端分别执行以下ping测试。
```
ping 10.0.5.1 -c 3
ping 10.0.5.2 -c 3
```
如果Wiregaurd Overlay网络设置正确，那么应该在双端都可以ping通。

### 在Client端创建iptables端口转发
在Client上执行：
```
python3 add-client.py $CLIENT_IP $HOST_IP $MAX_PORT > add-client.sh
bash add-client.sh
```
（这一步会运行较长时间）

### 在Server端创建iptables端口转发
在Server上执行：
```
python3 add-server.py $SERVER_IP $SERVER_IF $MAX_PORT > add-server.sh
bash add-server.sh
```
（这一步会运行较长时间）

## 完成
如果一切顺利，目前所有的设置都已经完成了。最后测试一下速度。
* 在Host端运行:
```
sudo iperf3 -s -p 800
```
* 在任意一台有网络的机器上测试转发速度:
```
iperf3 -c $SERVER_IP -p 800
```

from proxypool.api import app
from proxypool.schedule import Schedule

def main():
    #Schedule是一个调度器
    s = Schedule()
    #app是一个接口
    s.run()
    app.run()




if __name__ == '__main__':
    main()


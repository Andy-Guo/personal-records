plotnetcfg 是一个编译好的linux网络拓扑生成工具。
    "The open source tool called ``plotnetcfg`` can help to understand the relationship between the networking devices on a single host."
运行前需要安装绘制DOT语言脚本描述的图形的工具包graphviz: yum install -y graphviz    
在root下执行命令: plotnetcfg | dot -Tpdf > output.pdf
源码：https://github.com/jbenc/plotnetcfg 

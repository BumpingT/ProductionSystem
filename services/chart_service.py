"""图表报表生成服务"""
import os, json, tempfile, shutil, webbrowser
from config import YEN, ECHARTS_PATH


def _chart_html(stats, title=''):
    """生成 ECharts 图表 HTML"""
    t = stats['totals']; w = stats['by_worker']; d = stats['by_date']; p = stats['by_process']
    wj = json.dumps([x['q'] for x in w])
    dj = json.dumps([x['q'] for x in d])
    pj = json.dumps([x['q'] for x in p])
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><script src="echarts.min.js"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Microsoft YaHei,sans-serif;background:#f0f2f5;padding:20px}}
.sr{{display:flex;gap:12px;margin-bottom:16px}}
.sc{{flex:1;background:#fff;border-radius:8px;padding:14px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.l{{font-size:12px;color:#888}} .v{{font-size:20px;font-weight:700;color:#2c3e50;margin-top:4px}}
.o{{font-size:11px;color:#27ae60}} .cc{{background:#fff;border-radius:8px;padding:14px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.cb{{width:100%;min-height:220px}} table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{background:#f7f8fa;padding:6px 8px;text-align:left;border-bottom:2px solid #e8e8e8}}
td{{padding:5px 8px;border-bottom:1px solid #f0f0f0}} h3{{font-size:13px;color:#555;margin-bottom:8px}}
</style></head><body>
<h2 style="margin-bottom:12px">{title}</h2>
<div class="sr"><div class="sc"><div class="l">\u5de5\u4eba\u6570</div><div class="v">{t["w"]}</div></div>
<div class="sc"><div class="l">\u603b\u4ea7\u91cf</div><div class="v">{t["q"]}</div></div>
<div class="sc"><div class="l">\u603b\u5de5\u4ef7</div><div class="v">{YEN}{round(t["e"],2)}</div></div>
<div class="sc"><div class="l">\u8bb0\u5f55\u6570</div><div class="v">{t["r"]}</div></div></div>
<div class="cc"><h3>\u5de5\u4eba\u5de5\u8d44\u6392\u884c</h3><div id="w" class="cb"></div></div>
<div class="cc"><h3>\u65e5\u4ea7\u91cf\u8d8b\u52bf</h3><div id="d" class="cb"></div></div>
<div class="cc"><h3>\u5de5\u5e8f\u4ea7\u91cf\u5206\u5e03</h3><div id="p" class="cb"></div></div>
<script>
var wc=echarts.init(document.getElementById("w"));wc.setOption({{title:{{show:false}},tooltip:{{trigger:"axis",axisPointer:{{type:"shadow"}}}},xAxis:{{type:"value"}},yAxis:{{type:"category",data:{[x["worker"] for x in w]}}},series:[{{type:"bar",data:{wj},itemStyle:{{color:"#1a73e8",borderRadius:[0,4,4,0]}}}}]}});
var dc=echarts.init(document.getElementById("d"));dc.setOption({{title:{{show:false}},tooltip:{{trigger:"axis"}},xAxis:{{type:"category",data:{[x["record_date"] for x in d]}}},yAxis:{{type:"value"}},series:[{{type:"line",data:{[x["q"] for x in d]},smooth:true,lineStyle:{{color:"#27ae60"}},areaStyle:{{color:"#27ae60",opacity:.15}}}}]}});
var pc=echarts.init(document.getElementById("p"));pc.setOption({{title:{{show:false}},tooltip:{{trigger:"axis",axisPointer:{{type:"shadow"}}}},xAxis:{{type:"value"}},yAxis:{{type:"category",data:{[x["material"]+'-'+x["process_name"] for x in p]}}},series:[{{type:"bar",data:{pj},itemStyle:{{color:"#e67e22",borderRadius:[0,4,4,0]}}}}]}});
</script></body></html>'''


def gen_report(stats, title='\u751f\u4ea7\u8bb0\u5f55'):
    """生成报表并在浏览器打开"""
    html = _chart_html(stats, title)
    path = os.path.join(tempfile.gettempdir(), 'report.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    if os.path.exists(ECHARTS_PATH):
        shutil.copy(ECHARTS_PATH, os.path.join(tempfile.gettempdir(), 'echarts.min.js'))
    webbrowser.open('file://' + path)

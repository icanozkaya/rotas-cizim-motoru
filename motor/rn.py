import sys, pickle
sys.path.insert(0,'/home/claude/gungoren')
import rend
rend._flat = pickle.load(open('/tmp/claude-0/nb_flat.pkl','rb'))
x0,y0,x1,y1 = map(float, sys.argv[2].split(','))
rend.render(x0,y0,x1,y1, sys.argv[1], w=float(sys.argv[3]) if len(sys.argv)>3 else 20, minh=float(sys.argv[4]) if len(sys.argv)>4 else 0)

import pickle, sys, prev
from design import LAYERS
R, fr, H = pickle.load(open(sys.argv[3] if len(sys.argv)>3 else '/tmp/claude-0/cg_recs.pkl','rb'))
win=tuple(map(float,sys.argv[2].split(',')))
prev.render(R, LAYERS, win, sys.argv[1], w=float(sys.argv[4]) if len(sys.argv)>4 else 16)

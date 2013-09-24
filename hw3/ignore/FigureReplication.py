
data = np.loadtxt('figData.txt', dtype=[("NegSD-NegSR", np.float32), 
    ("NeuSD-NeuSR", np.float32), ("AmbSD-AmbSR", np.float32)])

NegMean = data["NegSD-NegSR"].mean()
NeuMean = data["NeuSD-NeuSR"].mean()
AmbMean = data["AmbSD-AmbSR"].mean()

NegStd = data["NegSD-NegSR"].std()
NeuStd= data["NeuSD-NeuSR"].std()
AmbStd= data["AmbSD-AmbSR"].std()


import numpy as np
import pandas as pd

columns=[12,13,46,15]
a=pd.DataFrame(np.arange(16).reshape(4,4),columns=columns)
b=[13,15]
a.loc[0,12]=None
a.loc[1,46]=None
a.loc[2,12]=None
print a
#print a[13]
c=a.loc[:,b]
print c.loc[0,13]
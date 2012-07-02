
import sys
from netCDF4 import Dataset
from wrf2kmz import *

from matplotlib import colors,cm

#clist=['white','#CCFF00','#66FF00',]
bounds=[0,1,5,10,25,50,100,250,500,1000]

basecmap=cm.jet
clist=[]
N=len(bounds)-1
for i in np.linspace(0,basecmap.N,N):
    clist.append(basecmap(float(i)/basecmap.N)[:-1])

cmap=colors.ListedColormap(clist)
norm=colors.BoundaryNorm(bounds,cmap.N)
cbarargs={'boundaries':bounds,'ticks':bounds,'spacing':'uniform'}

class LightningRaster(ZeroMaskedRaster):
    pass

class GCLightningRaster(LightningRaster):
    def __init__(self,*args,**kwargs):
        kwargs['derivedVar']=True
        super(GCLightningRaster,self).__init__(*args,**kwargs)

    def _readVarRaw(self,varname,istep):
        a=self._file.variables['LPOS']
        b=self._file.variables['LNEG']
        a=a+b
        return a.squeeze()

    def _getDescription(self):
        return 'GC'

class TotLightningRaster(LightningRaster):
    def __init__(self,*args,**kwargs):
        kwargs['derivedVar']=True
        super(TotLightningRaster,self).__init__(*args,**kwargs)

    def _readVarRaw(self,varname,istep):
        a=self._file.variables['LPOS'][istep,...]
        b=self._file.variables['LNEG'][istep,...]
        c=self._file.variables['LNEU'][istep,...]
        a=a+b+c
        return a.squeeze()

    def _getDescription(self):
        return 'Total Ground Lightning Density'

def test():
    subdomain={'centerlon':-80.874129,
               'centerlat':42.181647,
               'dx':500000,
               'dy':500000}
    f=Dataset(sys.argv[1],'r')
    lpos=LightningRaster(f,f.variables['LPOS'],name='LPOS',accum=True,accumsumhours=3,subdomain=subdomain)
    lneg=LightningRaster(f,f.variables['LNEG'],name='LNEG',accum=True,accumsumhours=3,subdomain=subdomain)
    
    n=ncKML()
    n.setViewFromRaster(lpos)
    n.groundOverlayFromRaster(lpos)
    n.groundOverlayFromRaster(lneg)
    n.savekmz('lightning.kmz')

def main():
    from optparse import OptionParser
    usage='''usage: %prog [-s centerlon centerlat width height] wrfout
centerlon,centerlat: center of subdomain in degrees lat/lon
width,height:        width/height of the subdomain in meters

Creates lightning.kmz from the contents of wrfout.
'''
    #parser=OptionParser(usage=usage)
    #parser.add_option('-s',action='store_true',dest='subdomain',help='Output only a subdomain',
    #                  default=False)
    
    #(opts,args) = parser.parse_args()
    
    class tmp(object):
        pass

    opts=tmp()
    opts.subdomain=False
    args=sys.argv[1:]
    if '-s' in args:
        args.remove('-s')
        opts.subdomain=True

    subdomain=None
    if opts.subdomain:
        if len(args) != 5:
            print >> sys.stderr, 'Invalid number of arguments for subdomain (-s)'
            sys.exit(1)
        subdomain = {'centerlon':float(args[0]),
                     'centerlat':float(args[1]),
                     'dx':float(args[2]),
                     'dy':float(args[3])}
        file=args[4]
    else:
        file=args[0]

    f=Dataset(file,'r')
    lpos=LightningRaster(f,f.variables['LPOS'],name='+GC',accum=True,accumsumhours=3,subdomain=subdomain,
                         cmap=cmap,norm=norm,colorbarargs=cbarargs,interp='sinc')
    lneg=LightningRaster(f,f.variables['LNEG'],name='-GC',accum=True,accumsumhours=3,subdomain=subdomain,
                         cmap=cmap,norm=norm,colorbarargs=cbarargs,interp='sinc')
    lneu=LightningRaster(f,f.variables['LNEU'],name='IC',accum=True,accumsumhours=None,subdomain=subdomain,
                         cmap=cmap,norm=norm,colorbarargs=cbarargs,interp='sinc')
    lgc=GCLightningRaster(f,f.variables['LPOS'],name='GC',accum=True,accumsumhours=3,subdomain=subdomain,
                          cmap=cmap,norm=norm,colorbarargs=cbarargs,interp='sinc')
    ltot=TotLightningRaster(f,f.variables['LPOS'],name='Total',accum=True,accumsumhours=3,subdomain=subdomain,
                         cmap=cmap,norm=norm,colorbarargs=cbarargs,interp='sinc')
    
    rain=ZeroMaskedRaster(f,f.variables['RAINNC'],name='RAINNC',accum=True,accumsumhours=3,subdomain=subdomain,
                          interp='sinc')
    snow=ZeroMaskedRaster(f,f.variables['SNOWH'],name='SNOWH',accum=True,accumsumhours=3,subdomain=subdomain,
                          interp='sinc')

    wind=Vector2Raster(f,f.variables['U'],f.variables['V'])


    n=ncKML()
    n.setViewFromRaster(lpos)
    n.groundOverlayFromRaster(lpos)
    n.groundOverlayFromRaster(lneg)
    n.groundOverlayFromRaster(lneu)
    n.groundOverlayFromRaster(lgc)
    n.groundOverlayFromRaster(ltot)
    n.groundOverlayFromRaster(rain)
    n.groundOverlayFromRaster(snow)
    n.groundOverlayFromRaster(wind)
    n.savekmz('lightning.kmz')

if __name__ == '__main__':
    main()
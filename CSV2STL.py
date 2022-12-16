#####################################################
########      RUTINA PARA CREAR STL          ########  
#####################################################


#Modulos y paquetes necesarios
from vtkmodules.all import *
import numpy as np
import pyvista as pv
import pandas as pd

#Importamos los datos de nuestro CSV
points = pd.read_csv('outputData.csv', delimiter = ',') #Estableciendo el delimitador con una coma
database = pd.DataFrame(points) 

#A veces al exportar el fichero se exporta una fila extra vacía que sera necesario identificar
lastArray = ['nan' for i in range(len(database.iloc[-1,:]))] #Creamos un array "vacio" como el que hipoteticamente se podria exportar
dataBaseLA = [str(database.iloc[-1,i]) for i in range(len(database.iloc[-1,:]))] #Registramos la ultima fila

if lastArray == dataBaseLA: #Con esto comparamos si las filas anteriores son iguales
    database = database.drop(database.index[-1]) #Si lo son la eliminamos de nuestra base de datos ya que estaba vacía

#Importamos todos los datos necesario
extrHub = database.iloc[:,[0,1]] #Extrados del Hub
intrHub = database.iloc[:,[2,3]] #Intrados del Hub
extrTip = database.iloc[:,[4,5]] #Extrados del Tip
intrTip = database.iloc[:,[6,7]] #Intrados del Tip
thetaHeights = database.iloc[:,8]*np.pi/180 #Calados a diferentes alturas
heights = database.iloc[:,9] #Alturas
rHub1 = database.iloc[-1,10] #Radio en el hub en 1
rHub2 = database.iloc[-1,11] #Radio en el hub en 2
crownPoints = database.iloc[:,[12,13,14]] #Puntos para crear la corona
chord = crownPoints.iloc[-1,0] #Cuerda
n = int(database.iloc[[0],17][0]) #Numero de alabes
angle = database.iloc[[0],18][0] #Angulo de posicion de alabes en corona
rShaft = database.iloc[[0],19][0] #Radio del eje
rFairingIn = database.iloc[0,20] #Radio interior del carenado
rFairingOut = database.iloc[1,20] #Radio exterior del carenado

# Construimos la estructura de la corona con una recta que une los puntos de rHub1 y rHub2
crownArray = [] #Inicializacion del array
for i in range(0,100):
    crownArray.append([crownPoints.iloc[i,0],crownPoints.iloc[i,1],crownPoints.iloc[i,2]]) #Añadimos todos los puntos al array
crownLineCloud = pv.PolyData(crownArray)
rotCrownLine = [] #Inicializacion del array para la rotacion de la anterior recta 
for i in range(360):
    rotCrownLine.append(crownLineCloud.rotate_x(i, point=(0, 0, 0), inplace=False)) #Añadimos los puntos
crownPoints2Mesh = crownLineCloud.merge(rotCrownLine) #Creamos la nube de puntos
crownLineMesh = crownPoints2Mesh.delaunay_2d(alpha=1e-1) #Creamos el mallado a partir de la nube de puntos

#Con este apartado diferenciamos si el radio del eje introducido es 0 o no nulo.
if rShaft == 0:
    disc1 = pv.Disc(center=(0,0,0), outer=rHub1, inner=0, normal=(1,0,0), c_res=360) #Disco entero para radio de eje 0 en 1
    disc2 = pv.Disc(center=(chord,0,0), outer=rHub2, inner=0, normal=(1,0,0), c_res=360) #Disco entero para radio de eje 0 en 2
    crownMesh = crownLineMesh.merge([disc1,disc2]) #Juntamos los discos junto con la estructura de la corona 
else:
    disc1 = pv.Disc(center=(0,0,0), outer=rHub1, inner=rShaft, normal=(1,0,0), c_res=360) #Disco hueco en 1 con eje no nulo
    disc2 = pv.Disc(center=(chord,0,0), outer=rHub2, inner=rShaft, normal=(1,0,0), c_res=360) #Disco hueco en 2 con eje no nulo
    cyl = pv.Tube(pointa=(chord, 0.0, 0.0), pointb=(0.0, 0.0, 0.0), resolution=360, radius=rShaft, n_sides=360) #Cilindro para rellenar el hueco del eje entre discos
    crownMesh = crownLineMesh.merge([disc1,disc2,cyl]) #Juntamos los discos y el cilindro junto con la estructura de la corona

disc1F = pv.Disc(center=(0,0,0), outer=rFairingOut, inner=rFairingIn, normal=(1,0,0), c_res=360) #Disco en 1 del carenado 
disc2F = pv.Disc(center=(chord,0,0), outer=rFairingOut, inner=rFairingIn, normal=(1,0,0), c_res=360) #Disco en 2 del carenado 
cylFairingIn = pv.Tube(pointa=(chord, 0.0, 0.0), pointb=(0.0, 0.0, 0.0), resolution=360, radius=rFairingIn, n_sides=360) #Cilindro interior del carenado
cylFairingOut = pv.Tube(pointa=(chord, 0.0, 0.0), pointb=(0.0, 0.0, 0.0), resolution=360, radius=rFairingOut, n_sides=360) #Cilindrio exterior del carenado
fairing = disc1F.merge([disc2F,cylFairingIn,cylFairingOut]) #Unimos caras del carenado

#Ahora creamos las caras del hub y del tip
face_h = [] #Inicializamos el array para la cara en el hub
face_t = [] #Inicializamos el array para la cara en el tip
for i in range(0,100): #Rellenamos las caras con una recta paramétrica entre los puntos del extrados e intrados para el hub
    face_h.append([[extrHub.iloc[i,0]+t*(intrHub.iloc[i,0]-extrHub.iloc[i,0]),
                    extrHub.iloc[i,1]+t*(intrHub.iloc[i,1]-extrHub.iloc[i,1]),
                    heights.iloc[0]] for t in np.linspace(0,1,100)]) #100 puntos entre punto simetrico de extrados e intrados
for i in range(0,100): #Rellenamos las caras con una recta paramétrica entre los puntos del extrados e intrados para el tip
    face_t.append([[extrTip.iloc[i,0]+t*(intrTip.iloc[i,0]-extrTip.iloc[i,0]),
                    extrTip.iloc[i,1]+t*(intrTip.iloc[i,1]-extrTip.iloc[i,1]),
                    heights.iloc[-1]] for t in np.linspace(0,1,100)]) #100 puntos entre punto simetrico de extrados e intrados
faceH = [point for part in face_h for point in part] #Homogeneizamos los arrays del hub
faceT = [point for part in face_t for point in part] #Homogeneizamos los arrays del tip
hubCloud = pv.PolyData(faceH) #Nube de puntos del hub
tipCloud = pv.PolyData(faceT) #Nube de puntos del tip
hubMesh = hubCloud.delaunay_2d() #Mallado del hub
tipMesh = tipCloud.delaunay_2d() #Mallado del tip

#Ahora creamos las caras del extrados e intrados
extrPoints = [] #Inicializamos el array para la cara en el extrados
intrPoints = [] #Inicializamos el array para la cara en el intrados
for j in range(0,101): # Los puntos de extrados e intrados en cada altura se desplazan con una matriz de rotacion con los calados correspondientes a cada altura
    for i in range(0,101):
        extrPoints.append([ extrHub.iloc[i,0]*np.cos(thetaHeights[j])-extrHub.iloc[i,1]*np.sin(thetaHeights[j]), #X
                            extrHub.iloc[i,0]*np.sin(thetaHeights[j])+extrHub.iloc[i,1]*np.cos(thetaHeights[j]), #Y
                             heights[j]]) #Z
        intrPoints.append([ intrHub.iloc[i,0]*np.cos(thetaHeights[j])-intrHub.iloc[i,1]*np.sin(thetaHeights[j]), #X
                            intrHub.iloc[i,0]*np.sin(thetaHeights[j])+intrHub.iloc[i,1]*np.cos(thetaHeights[j]), #Y
                            heights[j]]) #Z
extrCloud = pv.PolyData(extrPoints) #Nube de puntos de extrados
intrCloud = pv.PolyData(intrPoints) #Nube de puntos de intrados
extrMesh = extrCloud.delaunay_2d() #Mallado del extrados
intrMesh = intrCloud.delaunay_2d() #Mallado del intrados
mergedFoil = hubMesh.merge([tipMesh,extrMesh,intrMesh]) #Mallado del alabe con todas las caras unidas

#Ahora vamos a crear los alabes que se uniran a la estructura de la corona
mergedFoil.translate([0,0,rHub1], inplace=True) #Trasladamos el alabe principal una distancia Rhub1 en z
rotFoil = [] #Inicializamos array para incluir alabes rotados
for i in range(n): #Rotamos n veces por el angulo de desfase y añadimos el alabe al array
    rotFoil.append(mergedFoil.rotate_x(angle*i, point=(0, 0, 0), inplace=False))
crownFoils = mergedFoil.merge(rotFoil) #Unimos mallado del perfil principal con los rotados
rotorStage = crownFoils.merge(crownMesh) #Unimos mallado de los perfiles rotados con la estructura de la corona
completeStage = rotorStage.merge(fairing) #Unimos mallado de el rotor entero con el carenado del mismo

#Esta opcion esta desactivada, pero en un notebook sirve para representar el modelo 3D sin exportarlo
#completeStage.plot(color="orange")
#Por ultimo exportamos los modelos a formato STL
mergedFoil.save('compr_blade.stl') #Alabe de Rotor
rotorStage.save('rotor_stage.stl') #Etapa de Rotor
fairing.save('fairing.stl') #Carenado
completeStage.save('compr_stage.stl') #Etapa de compresor entero
#Fin del codigo
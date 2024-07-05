import os
import rasterio
from rasterio.mask import mask
from rasterio.warp import transform_bounds
from rasterio.features import geometry_mask
import geopandas as gpd
from shapely.geometry import box
from fiona.crs import from_epsg

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from io import BytesIO
from rasterio.plot import show
from matplotlib.colors import ListedColormap
from dotenv import load_dotenv
import cairosvg

import pandas as pd
from matplotlib.offsetbox import OffsetImage, AnnotationBbox



def rgba_to_hex(rgba_color):
    r, g, b, a = rgba_color
    r = int(r)
    g = int(g)
    b = int(b)
    a = int(a)
    hex_color = "#{:02X}{:02X}{:02X}".format(r, g, b)
    return hex_color

def color_pacum(pixelValue):
    if pixelValue == 0:
        return "none"
    elif 0.01 <= pixelValue <= 0.5:
        return rgba_to_hex((180, 215, 255, 255))
    elif 0.5 < pixelValue <= 1:
        return rgba_to_hex((117, 186, 255, 255))
    elif 1 < pixelValue <= 2:
        return rgba_to_hex((53, 154, 255, 255))
    elif 2 < pixelValue <= 3:
        return rgba_to_hex((4, 130, 255, 255))
    elif 3 < pixelValue <= 4:
        return rgba_to_hex((0, 105, 255, 255))
    elif 4 < pixelValue <= 5:
        return rgba_to_hex((0, 54, 127, 255))
    elif 5 < pixelValue <= 7:
        return rgba_to_hex((20, 143, 27, 255))
    elif 7 < pixelValue <= 10:
        return rgba_to_hex((26, 207, 5, 255))
    elif 10 < pixelValue <= 15:
        return rgba_to_hex((99, 237, 7, 255))
    elif 15 < pixelValue <= 20:
        return rgba_to_hex((255, 244, 43, 255))
    elif 20 < pixelValue <= 25:
        return rgba_to_hex((232, 220, 0, 255))
    elif 25 < pixelValue <= 30:
        return rgba_to_hex((240, 96, 0, 255))
    elif 30 < pixelValue <= 35:
        return rgba_to_hex((255, 127, 39, 255))
    elif 35 < pixelValue <= 40:
        return rgba_to_hex((255, 166, 106, 255))
    elif 40 < pixelValue <= 45:
        return rgba_to_hex((248, 78, 120, 255))
    elif 45 < pixelValue <= 50:
        return rgba_to_hex((247, 30, 84, 255))
    elif 50 < pixelValue <= 60:
        return rgba_to_hex((191, 0, 0, 255))
    elif 60 < pixelValue <= 70:
        return rgba_to_hex((136, 0, 0, 255))
    elif 70 < pixelValue <= 80:
        return rgba_to_hex((100, 0, 0, 255))
    elif 80 < pixelValue <= 90:
        return rgba_to_hex((194, 0, 251, 255))
    elif 90 < pixelValue <= 100:
        return rgba_to_hex((221, 102, 255, 255))
    elif 100 < pixelValue <= 125:
        return rgba_to_hex((235, 166, 255, 255))
    elif 125 < pixelValue <= 150:
        return rgba_to_hex((249, 230, 255, 255))
    elif 150 < pixelValue <= 300:
        return rgba_to_hex((212, 212, 212, 255))
    elif pixelValue > 300:
        return rgba_to_hex((0, 0, 0, 255))
    else:
        return "none"


def color_percent(pixelValue):
    if 0 <= pixelValue <= 0.1:
        return "#F9F788"
    elif 0.1 <= pixelValue <= 0.2:
        return "#D6D309"
    elif 0.2 <= pixelValue <= 0.3:
        return "#B08C00"
    elif 0.3 <= pixelValue <= 0.4:
        return "#B6F8A9"
    elif 0.4 <= pixelValue <= 0.5:
        return "#1DD41C"
    elif 0.5 <= pixelValue <= 0.6:
        return "#005200"
    elif 0.6 <= pixelValue <= 0.7:
        return "#359AFF"
    elif 0.7 <= pixelValue <= 0.8:
        return "#0069D2"
    elif 0.8 <= pixelValue <= 0.9:
        return "#00367F"
    elif 0.9 <= pixelValue <= 1:
        return "#100053"
    else:
        return "none"




def pacum_ec(raster, ec_gdf, prov_gdf, paute_gdf):
    # Abre el raster utilizando rasterio
    with rasterio.open(raster) as src:
        # Realiza el enmascaramiento del raster con las geometrías del shapefile
        out_image, out_transform = rasterio.mask.mask(src, ec_gdf.geometry, crop=True)
    #
    # Crear una lista de valores entre 0 y 1
    mmin = out_image.min()
    mmax = out_image.max()
    rang = int(100 * (mmax - mmin))
    values = np.linspace(int(mmin), int(mmax), rang)  # Asegurarse de que haya suficientes valores en el rango
    #
    # Crear una lista de colores utilizando la función color
    colors = [color_pacum(value) for value in values]
    #
    # Crear un objeto ListedColormap basado en la lista de colores
    cmap_custom = ListedColormap(colors)
    #
    # Crea una figura de Matplotlib y muestra el raster enmascarado
    plt.figure(figsize=(8, 8))
    plt.margins(0)
    ax = plt.gca()
    show(out_image, transform=out_transform, ax=plt.gca(), cmap=cmap_custom)
    prov_gdf.plot(ax=plt.gca(), color='none', edgecolor='black', linewidth=0.2)
    ec_gdf.plot(ax=plt.gca(), color='none', edgecolor='black', linewidth=1)
    paute_gdf.plot(ax=plt.gca(), color='none', edgecolor='black', linewidth=2)
    #
    # Establecer límites en los ejes x e y   
    plt.xlim(-81.3, -74.9)
    plt.ylim(-5.2, 1.6)
    #
    # Ajustar el tamaño de los números de los ejes
    ax.tick_params(axis='both', which='major', labelsize=15)
    #
    # Añadir un título a la figura
    #plt.title("Ecuador Continental", fontsize=22)
    #
    # Save the figure
    plt.savefig("ecuador.png", bbox_inches='tight', pad_inches=0.2)


def pacum_area(raster, ec_gdf, rp_gdf, rs_gdf, puntos_gdf):
    # Abre el raster utilizando rasterio
    with rasterio.open(raster) as src:
        # Realiza el enmascaramiento del raster con las geometrías del shapefile
        out_image, out_transform = rasterio.mask.mask(src, ec_gdf.geometry, crop=True)
    #
    # Crear una lista de valores entre 0 y 1
    mmin = out_image.min()
    mmax = out_image.max()
    rang = int(100 * (mmax - mmin))
    values = np.linspace(int(mmin), int(mmax), rang)   # Asegurarse de que haya suficientes valores en el rango
    #
    # Crear una lista de colores utilizando la función color
    colors = [color_pacum(value) for value in values]
    #
    # Crear un objeto ListedColormap basado en la lista de colores
    cmap_custom = ListedColormap(colors)
    #
    # Crea una figura de Matplotlib y muestra el raster enmascarado
    plt.figure(figsize=(8, 8))
    plt.margins(0)
    ax = plt.gca()
    show(out_image, transform=out_transform, ax=plt.gca(), cmap=cmap_custom)
    puntos_gdf.plot(ax=plt.gca(), color='red', markersize=10, label="Puntos afectados")
    rs_gdf.plot(ax=plt.gca(), color='black', edgecolor='black', linewidth=0.2, label="Rios")
    rp_gdf.plot(ax=plt.gca(), color='black', edgecolor='black', linewidth=1)
    puntos_gdf.plot(ax=plt.gca(), color='red', markersize=10)

    # Establecer límites en los ejes x e y   
    plt.xlim(-78.55, -78.05)
    plt.ylim(-1.3, -1.5)
    #plt.axis("off")
    # Ajustar el tamaño de los números de los ejes
    ax.tick_params(axis='both', which='major', labelsize=7)
    #
    # Añadir un título a la figura
    #plt.title("Zona afectada", fontsize=10)
    #
    # Agregar la leyenda en la parte inferior
    plt.legend(loc='lower right')
    #
    # Save the figure
    plt.savefig("area.png", bbox_inches='tight', pad_inches=0.2)


def join_images(img1, img2, name):
    # Cargar las imágenes
    imagen1 = mpimg.imread(img1)
    imagen2 = mpimg.imread(img2)
    # Crear una nueva figura con una cuadrícula personalizada
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5), gridspec_kw={'width_ratios': [1, 2]})
    # Mostrar la primera imagen en la primera subtrama
    ax1.imshow(imagen1)
    ax1.axis('off')
    ax1.set_aspect(aspect='auto')
    # Mostrar la segunda imagen en la segunda subtrama
    ax2.imshow(imagen2)
    ax2.axis('off')
    ax2.set_aspect(aspect='auto')
    # Ajustar el espacio entre las subtramas
    plt.tight_layout()
    # Guardar la figura en un archivo de imagen
    plt.savefig(name)



def get_pacum_subbasin(raster_file, shp_file, field):
    # Cargar el shapefile de cuencas hidrográficas
    cuencas = shp_file
    resultados = pd.DataFrame(columns=['subbasin', 'pacum'])
    #
    # Abrir el archivo raster
    with rasterio.open(raster_file) as src:
        # Reproyectar el shapefile para que coincida con la proyección del raster
        cuencas = cuencas.to_crs(src.crs)
        #
        # Leer los valores del raster que intersectan con las geometrías de las cuencas
        for index, row in cuencas.iterrows():
            geom = row.geometry
            #
            # Máscara del raster basado en la geometría de la cuenca
            out_image, out_transform = mask(src, [geom], crop=True)
            out_image[out_image < 0] = 0
            #
            # Calcular el valor promedio de precipitación dentro de la cuenca
            avg_precipitation = round(np.nanmean(out_image), 2)
            #
            # Agregar los resultados al DataFrame
            resultados = resultados.append({'subbasin': f"Rio {row[field]}", 'pacum': avg_precipitation}, ignore_index=True)
    #
    return(resultados)



def asm_plot(gdf, prov_gdf, ec_gdf, area_gdf):
    # Generate the color bar
    mmin = gdf["asm"].min()
    mmax = gdf["asm"].max()
    rang = int(100*(mmax - mmin)) 
    values = np.linspace(mmin, mmax, int(rang))  
    #
    # Crear una lista de colores utilizando la función color
    colorfun = color_percent
    colors = [colorfun(value) for value in values]
    #
    # Crear un objeto ListedColormap basado en la lista de colores
    cmap_custom = ListedColormap(colors)
    #
    # Crea una figura de Matplotlib y muestra el raster enmascarado
    plt.figure(figsize=(8, 8))
    plt.margins(0)
    ax = plt.gca()
    #
    # Graficar el GeoDataFrame utilizando el campo especificado
    gdf.plot(column="asm", legend=False, cmap=cmap_custom, figsize=(8, 8))
    prov_gdf.plot(ax=plt.gca(), color='none', edgecolor='black', linewidth=0.2)
    ec_gdf.plot(ax=plt.gca(), color='none', edgecolor='black', linewidth=1)
    area_gdf.plot(ax=plt.gca(), color='none', edgecolor='black', linewidth=2)
    #
    # Establecer límites en los ejes x e y   
    plt.xlim(-81.3, -74.9)
    plt.ylim(-5.2, 1.6)
    #
    # Ajustar el tamaño de los números de los ejes
    ax.tick_params(axis='both', which='major', labelsize=15)
    #
    # Save the figure
    plt.savefig("asm_ec.png", bbox_inches='tight', pad_inches=0.2)




    
def asm_area_plot(gdf, puntos_gdf, rp_gdf, rs_gdf):
    # Generate the color bar
    mmin = gdf["asm"].min()
    mmax = gdf["asm"].max()
    rang = int(100*(mmax - mmin)) 
    values = np.linspace(mmin, mmax, int(rang))  
    #
    # Crear una lista de colores utilizando la función color
    colorfun = color_percent
    colors = [colorfun(value) for value in values]
    #
    # Crear un objeto ListedColormap basado en la lista de colores
    cmap_custom = ListedColormap(colors)
    #
    # Crea una figura de Matplotlib y muestra el raster enmascarado
    plt.figure(figsize=(8, 8))
    plt.margins(0)
    ax = plt.gca()
    #
    # Graficar el GeoDataFrame utilizando el campo especificado
    gdf.plot(column="asm", legend=False, cmap=cmap_custom, figsize=(8, 8))
    puntos_gdf.plot(ax=plt.gca(), color='red', markersize=10, label="Puntos afectados")
    rs_gdf.plot(ax=plt.gca(), color='black', edgecolor='black', linewidth=0.2, label="Rios")
    rp_gdf.plot(ax=plt.gca(), color='black', edgecolor='black', linewidth=1)
    puntos_gdf.plot(ax=plt.gca(), color='red', markersize=10)

    # Establecer límites en los ejes x e y   
    plt.xlim(-78.55, -78.05)
    plt.ylim(-1.3, -1.5)
    #
    # Ajustar el tamaño de los números de los ejes
    ax.tick_params(axis='both', which='major', labelsize=7)
    #
    # Agregar la leyenda en la parte inferior
    plt.legend(loc='lower right')
    #
    # Save the figure
    plt.savefig("asm_area.png", bbox_inches='tight', pad_inches=0.2)



def geoglows_plot(ec_gdf, prov_gdf, drainage_gdf, df, area_gdf):
    # Crear una figura y ejes de Matplotlib
    plt.figure(figsize=(8, 8))
    plt.margins(0)
    ax = plt.gca()
    #
    # Graficar el archivo SHP
    prov_gdf.plot(ax=plt.gca(), color='none', edgecolor='black', linewidth=0.2)
    ec_gdf.plot(ax=plt.gca(), color='none', edgecolor='black', linewidth=1)
    drainage_gdf.plot(ax=plt.gca(), color='blue', edgecolor='blue', linewidth=0.3)
    #
    # Configurar la ruta a los archivos SVG para cada clase 'alert'
    svg_mapping = {
        'R0': 'svg/0.svg',
        'R2': 'svg/2.svg',
        'R5': 'svg/5.svg',
        'R10': 'svg/10.svg',
        'R25': 'svg/25.svg',
        'R50': 'svg/50.svg',
        'R100': 'svg/100.svg'}
    #
    # Graficar los puntos utilizando archivos SVG como marcadores
    for index, row in df.iterrows():
        lat = row['latitude']
        lon = row['longitude']
        alert = row['alert']
        #   
        # Obtener la ruta del archivo SVG correspondiente
        svg_path = svg_mapping.get(alert, 'default_icon.svg')
        #
        # Convertir el archivo SVG en una imagen temporal (PNG)
        temp_png_path = 'temp_icon.png'
        cairosvg.svg2png(url=svg_path, write_to=temp_png_path)
        #
        # Cargar la imagen PNG como un OffsetImage
        img = OffsetImage(plt.imread(temp_png_path), zoom=0.5)
        ab = AnnotationBbox(img, (lon, lat), frameon=False)
        #
        # Agregar el marcador al gráfico
        plt.gca().add_artist(ab)
    #
    area_gdf.plot(ax=plt.gca(), color='none', edgecolor='black', linewidth=2)
    #
    # Establecer límites en los ejes x e y   
    plt.xlim(-81.3, -74.9)
    plt.ylim(-5.2, 1.6)
    #
    # Ajustar el tamaño de los números de los ejes
    ax.tick_params(axis='both', which='major', labelsize=15)
    plt.margins(0)
    #
    # Save the figure
    plt.savefig("geoglows_ec.png", bbox_inches='tight', pad_inches=0.2)





def geoglows_plot_area(puntos_gdf, rs_gdf, rp_gdf, df):
    # Crear una figura y ejes de Matplotlib
    plt.figure(figsize=(8, 8))
    ax = plt.gca()
    
    # Establecer límites en los ejes x e y   
    plt.xlim(-78.55, -78.05)
    plt.ylim(-1.5, -1.3)
    
    # Configurar la ruta a los archivos SVG para cada clase 'alert'
    svg_mapping = {
        'R0': 'svg/0.svg',
        'R2': 'svg/2.svg',
        'R5': 'svg/5.svg',
        'R10': 'svg/10.svg',
        'R25': 'svg/25.svg',
        'R50': 'svg/50.svg',
        'R100': 'svg/100.svg'
    }
    
    # Graficar puntos afectados
    puntos_gdf.plot(ax=ax, color='red', markersize=10, label="Puntos afectados")
    
    # Graficar los puntos utilizando archivos SVG como marcadores
    for index, row in df.iterrows():
        lat = row['latitude']
        lon = row['longitude']
        alert = row['alert']
        
        # Obtener la ruta del archivo SVG correspondiente
        svg_path = svg_mapping.get(alert, 'default_icon.svg')
        
        # Convertir el archivo SVG en una imagen temporal (PNG)
        temp_png_path = 'temp_icon.png'
        cairosvg.svg2png(url=svg_path, write_to=temp_png_path)
        
        # Cargar la imagen PNG como un OffsetImage
        img = OffsetImage(plt.imread(temp_png_path), zoom=0.5)
        ab = AnnotationBbox(img, (lon, lat), frameon=False)
        
        # Agregar el marcador al gráfico
        ax.add_artist(ab)
    
    # Graficar rios y otros puntos
    rs_gdf.plot(ax=ax, color='black', edgecolor='black', linewidth=0.2, label="Rios")
    rp_gdf.plot(ax=ax, color='black', edgecolor='black', linewidth=1)
    puntos_gdf.plot(ax=ax, color='red', markersize=10)
    
    # Ajustar el tamaño de los números de los ejes
    ax.tick_params(axis='both', which='major', labelsize=7)
    
    # Agregar la leyenda en la parte inferior
    plt.legend(loc='lower right')
    
    # Guardar la figura
    plt.savefig("geoglows_area.png", bbox_inches='tight', pad_inches=0.1)
    plt.show()
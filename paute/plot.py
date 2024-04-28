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

from io import BytesIO
from rasterio.plot import show
from matplotlib.colors import ListedColormap
from dotenv import load_dotenv
import cairosvg


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



def pacum_ec(raster, ec_gdf, prov_gdf, paute_gdf):
    # Abre el raster utilizando rasterio
    with rasterio.open(raster) as src:
        # Realiza el enmascaramiento del raster con las geometrías del shapefile
        out_image, out_transform = rasterio.mask.mask(src, ec_gdf.geometry, crop=True)
    #
    # Crear una lista de valores entre 0 y 1
    mmin = out_image.min()
    mmax = out_image.max()
    rang = 100*(mmax - mmin)
    values = np.linspace(mmin, mmax, rang)  # Asegurarse de que haya suficientes valores en el rango
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
    show(out_image, transform=out_transform, ax=plt.gca(), cmap=cmap_custom)
    prov_gdf.plot(ax=plt.gca(), color='none', edgecolor='black', linewidth=0.2)
    ec_gdf.plot(ax=plt.gca(), color='none', edgecolor='black', linewidth=1)
    paute_gdf.plot(ax=plt.gca(), color='none', edgecolor='black', linewidth=2)

    # Establecer límites en los ejes x e y   
    plt.xlim(-81.3, -74.9)
    plt.ylim(-5.2, 1.6)
    #plt.axis("off")
    #
    # Añadir un título a la figura
    plt.title("Ecuador Continental", fontsize=18)
    #
    # Save the figure
    plt.savefig("ecuador.png", bbox_inches='tight', pad_inches=0.2)


def pacum_paute(raster, paute_gdf, rp_gdf, rs_gdf, embalses_gdf):
    # Abre el raster utilizando rasterio
    with rasterio.open(raster) as src:
        # Realiza el enmascaramiento del raster con las geometrías del shapefile
        out_image, out_transform = rasterio.mask.mask(src, paute_gdf.geometry, crop=True)
    #
    # Crear una lista de valores entre 0 y 1
    mmin = out_image.min()
    mmax = out_image.max()
    rang = 100*(mmax - mmin)
    values = np.linspace(mmin, mmax, rang)  # Asegurarse de que haya suficientes valores en el rango
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
    show(out_image, transform=out_transform, ax=plt.gca(), cmap=cmap_custom)
    rs_gdf.plot(ax=plt.gca(), color='black', edgecolor='black', linewidth=0.2)
    rp_gdf.plot(ax=plt.gca(), color='black', edgecolor='black', linewidth=1, label="Rios")
    plt.legend(loc='lower right')
    paute_gdf.plot(ax=plt.gca(), color='none', edgecolor='black', linewidth=2)
    embalses_gdf.plot(ax=plt.gca(), color='red', markersize=50, label="Embalses")

    # Establecer límites en los ejes x e y   
    plt.xlim(-79.4, -78.2)
    plt.ylim(-3.3, -2.25)
    #plt.axis("off")
    #
    # Añadir un título a la figura
    plt.title("Cuenca del río Paute", fontsize=18)
    #
    # Agregar la leyenda en la parte inferior
    #plt.legend(loc='lower right')
    handles, labels = plt.gca().get_legend_handles_labels()
    plt.legend(handles, labels, loc='lower right')
    #
    # Save the figure
    plt.savefig("paute.png", bbox_inches='tight', pad_inches=0.2)


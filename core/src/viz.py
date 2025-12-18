import plotly.graph_objs as go
from src.wall import *
import pandas as pd


import pandas as pd
import plotly.graph_objects as go

def create_volume_trace(_id,element_type,x_min, x_max, y_min, y_max, z_min, z_max, color, opacity):
    x = [x_min, x_min, x_max, x_max, x_min, x_min, x_max, x_max]
    y = [y_min, y_max, y_max, y_min, y_min, y_max, y_max, y_min]
    z = [z_min, z_min, z_min, z_min, z_max, z_max, z_max, z_max]
    i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
    j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
    k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
    
    return go.Mesh3d(
        x=x,
        y=y,
        z=z,
        i=i,
        j=j,
        k=k,
        opacity=1,
        color=color,
        flatshading=True,
        text=f'{element_type} : {_id}  [ {int(z_max-z_min)} x {int(x_max-x_min)} ]'
    )

        

def fig_3D_lattice(lattice):

    traces = []
    # Créer les traces lattice  
    df = pd.DataFrame(lattice.as_dict()['elements'])
    for index, row in df.iterrows():
        if row['element_type']=='slat':
            color = '#DA5D42'
        elif row['element_type']=='batten':
            color = '#DA5D42'
        elif row['element_type']=='insulation':
            color = '#DA9342'
        elif row['element_type']=='renfort':
            color =  '#DA5D42'#'#429EDA'
        else: 
            color = 'rgba(255,0,0,0.5)'
        trace = create_volume_trace(row['id'],row['element_type'],row['x_min'], row['x_max'], row['y_min'], row['y_max'], row['z_min'], row['z_max'],color, 1)
        traces.append(trace)            

    # Calculer les limites minimales et maximales pour chaque axe
    x_min = df[['x_min', 'x_max']].values.min()
    x_max = df[['x_min', 'x_max']].values.max()
    y_min = df[['y_min', 'y_max']].values.min()
    y_max = df[['y_min', 'y_max']].values.max()
    z_min = df[['z_min', 'z_max']].values.min()
    z_max = df[['z_min', 'z_max']].values.max()

    # Définir les limites globales pour chaque axe
    axis_min = min(x_min, y_min, z_min)
    axis_max = max(x_max, y_max, z_max)

    # Créer la figure
    fig = go.Figure(data=traces)

    # Mettre à jour la mise en page avec les mêmes limites pour chaque axe
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[axis_min, axis_max]),
            yaxis=dict(range=[axis_min, axis_max]),
            zaxis=dict(range=[axis_min, axis_max]),
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=0)  # Top view (X-Y Plane)
            )
        ),
        #width=1200,  # Ajustez la largeur du plot
        height=600,  # Ajustez la hauteur du plot
        margin=dict(
            l=0,  # left margin
            r=0,  # right margin
            t=0,  # top margin
            b=0   # bottom margin
        )
    )

    # Afficher la figure
    #fig.show()
    return fig



material_color = {
    'Douglas': 'saddlebrown',
    'Mineral Wool': 'khaki',
    'OSB': 'goldenrod',
    'CLT': 'peru',
    'Laine de bois': 'lightgreen',
    'BA13': 'grey',
}
    
def fig_3D_buildup_old(buildup):

    material_color_dict = {
        'BA13': '#C0C0C0',                        # Gris clair standard
        'Douglas': '#F4D677',                     # Jaune bois
        'Mineral Wool': '#F9EBC3',                 # Crème / jaune pâle
        'fibro ciment': '#BDD5D5'                 # Bleu-gris pastel
    }


    traces = []
    # Créer les traces lattice 
    df_lattice = pd.DataFrame(buildup.lattice.as_dict()['elements'])
    dfs = [df_lattice]
    for index, row in df_lattice.iterrows():
        if row['element_type'] == 'slat':
            color = '#E6D6C2'#'#DA5D42'
            opacity = 1  
        elif row['element_type'] == 'insulation':
            color = '#C29453' #'#DA9342'
            opacity = 1  

        else:
            opacity = 1  # Opacité par défaut
        trace = create_volume_trace(row['id'],row['element_type'],row['x_min'], row['x_max'], row['y_min'], row['y_max'], row['z_min'], row['z_max'],color, opacity)
        traces.append(trace)

    # Créer les traces des layers 
    for layer in buildup.layers:
        
        df_layer = pd.DataFrame(layer.as_dict()['elements'])
        dfs.append(df_layer)
        for index, row in df_layer.iterrows():
            color = material_color_dict[layer.materials[row['element_type']]]
            opacity = 1  
            trace = create_volume_trace(row['id'],row['element_type'],row['x_min'], row['x_max'], row['y_min'], row['y_max'], row['z_min'], row['z_max'],color, opacity)
            traces.append(trace)
            

      # Exemple

    # Pour les concaténer en un seul DataFrame:
    df = pd.concat(dfs, ignore_index=True)
    # Calculer les limites minimales et maximales pour chaque axe
    x_min = df[['x_min', 'x_max']].values.min()
    x_max = df[['x_min', 'x_max']].values.max()
    y_min = df[['y_min', 'y_max']].values.min()
    y_max = df[['y_min', 'y_max']].values.max()
    z_min = df[['z_min', 'z_max']].values.min()
    z_max = df[['z_min', 'z_max']].values.max()

    # Définir les limites globales pour chaque axe
    axis_min = min(x_min, y_min, z_min)
    axis_max = max(x_max, y_max, z_max)

    # Créer la figure
    fig = go.Figure(data=traces)

    # Mettre à jour la mise en page avec les mêmes limites pour chaque axe
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[axis_min, axis_max]),
            yaxis=dict(range=[axis_min, axis_max]),
            zaxis=dict(range=[axis_min, axis_max]),
            xaxis_title='X',
            yaxis_title='Y',
            zaxis_title='Z',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=0)  # Top view (X-Y Plane)
            )
        ),
        #width=1200,  # Ajustez la largeur du plot
        height=600,  # Ajustez la hauteur du plot
        margin=dict(
            l=0,  # left margin
            r=0,  # right margin
            t=0,  # top margin
            b=0   # bottom margin
        )
    )

    # Afficher la figure
    #fig.show()
    return fig


import pandas as pd
import plotly.graph_objects as go

def fig_3D_buildup(buildup):
    """
    Génère une figure Plotly 3D interactive.
    Légende précise : "[X] Layer X lattice" pour la structure, "[X] Nom" pour le reste.
    """
    
    material_color_dict = {
        'BA13': '#C0C0C0', 'Douglas': '#F4D677', 'Mineral Wool': '#F9EBC3',
        'fibro ciment': '#BDD5D5', 'OSB': '#D2B48C', 'Laine de bois': '#C29453',
        'default': '#CCCCCC'
    }

    traces = []
    dfs = []

    # --- A. TRAITEMENT DE LA LATTICE (COUCHES 1 à 5) ---
    if buildup.lattice:
        df_lattice = pd.DataFrame(buildup.lattice.as_dict()['elements'])
        dfs.append(df_lattice)
        
        # On groupe par 'layer' (1, 2, 3, 4, 5...)
        if 'layer' in df_lattice.columns:
            grouped_lattice = df_lattice.groupby('layer')
            
            for layer_idx, group in grouped_lattice:
                # NOMMAGE SPÉCIFIQUE DEMANDÉ
                layer_group_name = f"[{layer_idx}] Layer {layer_idx}"
                
                show_legend_once = True
                
                for index, row in group.iterrows():
                    if row['element_type'] == 'slat':
                        color = '#E6D6C2'
                    elif row['element_type'] == 'insulation':
                        color = '#C29453'
                    else:
                        color = 'gray'

                    trace = create_volume_trace(
                        row['id'], row['element_type'], 
                        row['x_min'], row['x_max'], row['y_min'], row['y_max'], row['z_min'], row['z_max'], 
                        opacity=1, color=color
                    )
                    
                    trace.update(
                        legendgroup=layer_group_name,
                        name=layer_group_name,
                        showlegend=show_legend_once
                    )
                    show_legend_once = False
                    traces.append(trace)
        else:
            # Fallback si la colonne 'layer' n'existe pas (cas rare)
            print("Attention: Colonne 'layer' manquante dans Lattice elements")

    # --- B. TRAITEMENT DES COUCHES ADDITIONNELLES ---
    for layer in buildup.layers:
        elements = layer.as_dict().get('elements', [])
        if not elements:
            continue
        df_layer = pd.DataFrame(elements)
        dfs.append(df_layer)
        
        layer_group_name = f"[{layer.layer_index}] {layer.name}"
        show_legend_once = True

        for index, row in df_layer.iterrows():
            mat_name = layer.materials.get(row['element_type'], 'default')
            color = material_color_dict.get(mat_name, material_color_dict['default'])
            
            trace = create_volume_trace(
                row['id'], row['element_type'], 
                row['x_min'], row['x_max'], row['y_min'], row['y_max'], row['z_min'], row['z_max'], 
                opacity=1, color=color
            )
            
            trace.update(
                legendgroup=layer_group_name,
                name=layer_group_name,
                showlegend=show_legend_once
            )
            show_legend_once = False
            traces.append(trace)

    # --- C. CALCUL LIMITES & FIGURE ---
    if dfs:
        df = pd.concat(dfs, ignore_index=True)
        x_min, x_max = df['x_min'].min(), df['x_max'].max()
        y_min, y_max = df['y_min'].min(), df['y_max'].max()
        z_min, z_max = df['z_min'].min(), df['z_max'].max()
        axis_min = min(x_min, y_min, z_min)
        axis_max = max(x_max, y_max, z_max)
    else:
        axis_min, axis_max = 0, 1000

    # --- 4. FIGURE ---
    fig = go.Figure(data=traces)
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[axis_min, axis_max], title='X'),
            yaxis=dict(range=[axis_min, axis_max], title='Y'),
            zaxis=dict(range=[axis_min, axis_max], title='Z'),
            aspectmode='cube', # Astuce pour ne pas déformer la 3D
            camera=dict(eye=dict(x=1.5, y=1.5, z=0.5))
        ),
        height=800,
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(title="Couches (Cliquer pour masquer)") # Titre légende
    )

    return fig


import plotly.graph_objects as go

import plotly.graph_objects as go

def fig_section_view(buildup, view_type='vertical', cut_pos=None):
    """
    Génère une vue technique 2D avec proportions réelles (1:1) et cadrage automatique.
    - view_type='vertical' : Coupe YZ (Élévation/Coupe technique)
    - view_type='horizontal' : Coupe XY (Plan)
    """
    
    material_color_dict = {
        'BA13': '#C0C0C0', 'Douglas': '#F4D677', 'Mineral Wool': '#F9EBC3',
        'fibro ciment': '#BDD5D5', 'OSB': '#D2B48C', 'Laine de bois': '#C29453',
        'default': '#CCCCCC'
    }

    fig = go.Figure()
    
    if cut_pos is None:
        if view_type == 'vertical': cut_pos = 100 
        else: cut_pos = 1500 

    # --- 1. AJOUT DES FORMES (SHAPES) ---
    def add_layer_shapes(elements, context="layer", obj=None):
        for el in elements:
            is_visible = False
            if view_type == 'vertical': 
                if el['x_min'] <= cut_pos <= el['x_max']:
                    is_visible = True
                    x0, y0 = el['y_min'], el['z_min']
                    x1, y1 = el['y_max'], el['z_max']
            elif view_type == 'horizontal': 
                if el['z_min'] <= cut_pos <= el['z_max']:
                    is_visible = True
                    x0, y0 = el['y_min'], el['x_min']
                    x1, y1 = el['y_max'], el['x_max']
            
            if not is_visible: continue

            color = '#CCCCCC'
            if context == "lattice":
                if el['element_type'] == 'slat': color = '#E6D6C2'
                elif el['element_type'] == 'insulation': color = '#C29453'
            elif context == "layer" and obj:
                mat = obj.materials.get(el['element_type'], 'default')
                color = material_color_dict.get(mat, '#CCCCCC')

            fig.add_shape(
                type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
                line=dict(color="black", width=1),
                fillcolor=color, opacity=1, layer="below" 
            )

    if buildup.lattice:
        add_layer_shapes(buildup.lattice.as_dict()['elements'], "lattice")
    for layer in buildup.layers:
        add_layer_shapes(layer.as_dict().get('elements', []), "layer", layer)

    # --- 2. CALCUL DU ZOOM (BOUNDING BOX) ---
    x_range = [0, 1000]
    y_range = [0, 1000]
    
    if fig.layout.shapes:
        xs = [s.x0 for s in fig.layout.shapes] + [s.x1 for s in fig.layout.shapes]
        ys = [s.y0 for s in fig.layout.shapes] + [s.y1 for s in fig.layout.shapes]
        
        # Petite marge technique (50mm)
        margin = 50 
        if xs and ys:
            x_range = [min(xs) - margin, max(xs) + margin]
            y_range = [min(ys) - margin, max(ys) + margin]

    # --- 3. CALCUL TAILLE DYNAMIQUE DE LA FIGURE (POUR RATIO 1:1) ---
    dx = x_range[1] - x_range[0]
    dy = y_range[1] - y_range[0]
    if dy == 0: dy = 1
    
    # Ratio géométrique réel
    aspect_ratio = dx / dy
    
    # Hauteur fixe de base (ex: 800px pour bien voir)
    base_height = 800
    
    # Largeur calculée pour respecter le ratio + place pour les axes
    # On s'assure d'une largeur min de 500px pour que ce soit lisible
    calculated_width = int(base_height * aspect_ratio) + 100 # +100px pour marge axes
    final_width = max(500, calculated_width)

    # --- 4. CONFIGURATION FINALE ---
    ytitle = "Z (Hauteur) [mm]" if view_type == 'vertical' else "X (Épaisseur) [mm]"
    
    fig.update_layout(
        title=f"Vue {view_type.capitalize()} (Coupe à {cut_pos} mm)",
        
        xaxis=dict(
            title="Y (Longueur) [mm]",
            showgrid=False, zeroline=True, zerolinecolor='black',
            
            # PROPORTION RESPECTÉE
            scaleanchor='y', scaleratio=1,
            
            range=x_range,
            tickmode='auto', nticks=15
        ),
        
        yaxis=dict(
            title=ytitle, 
            showgrid=False, zeroline=True, zerolinecolor='black',
            
            range=y_range,
            tickmode='auto', nticks=15
        ),

        plot_bgcolor='white',
        
        # TAILLE INTELLIGENTE
        height=base_height,
        width=final_width,
        
        margin=dict(l=50, r=50, t=50, b=50),
        
        # Pas de légende car c'est un dessin technique
        showlegend=False 
    )
    
    # Scatter invisible pour forcer le rendu correct des axes si shapes seules
    fig.add_trace(go.Scatter(x=x_range, y=y_range, mode='markers', marker=dict(opacity=0)))

    return fig





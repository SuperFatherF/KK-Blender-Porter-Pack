import bpy
import json
from pathlib import Path
from bpy.props import (
        StringProperty,
        BoolProperty,
        FloatProperty,
        EnumProperty,
        )
from bpy_extras.io_utils import (
        ImportHelper,
        ExportHelper,
        orientation_helper,
        path_reference_mode,
        axis_conversion,
        )

########## ERRORS ##########
def kk_folder_error(self, context):
    self.layout.label(text="Please make sure to open the folder that was exported. (Hint: go into the folder before confirming)")

########## FUNCTIONS ##########
def checks(directory):
    # "Borrowed" some logic from importeverything.py :P
    file_list = Path(directory).glob('*.*')
    files = [file for file in file_list if file.is_file()]
    filtered_files = []

    json_file_missing = True
    for file in files:
        if 'KK_SMRData.json' in str(file):
            json_file_path = str(file)
            json_file = open(json_file_path)
            json_file_missing = False
    
    if json_file_missing:
        bpy.context.window_manager.popup_menu(kk_folder_error, title="Error", icon='ERROR')
        return True

    return False

def load_smr_data(directory):
    # "Borrowed" some logic from importeverything.py :P
    file_list = Path(directory).glob('*.*')
    files = [file for file in file_list if file.is_file()]

    for file in files:
        if 'KK_SMRData.json' in str(file):
            json_file_path = str(file)
            json_file = open(json_file_path)
            json_smr_data = json.load(json_file)
            
    separate_clothes(json_smr_data)
    separate_body(json_smr_data)
            
def separate_clothes(json_smr_data): 
    #Get Clothes and it's object data
    clothes = bpy.data.objects['Clothes']
    clothes_data = clothes.data
    
    #Pass 1: To make sure each material has a mesh
    #Select the Clothes object and remove it's unused material slots
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    clothes.select_set(True)
    bpy.ops.object.material_slot_remove_unused()
    
    #To keep track if a mesh has been separated already
    separated_meshes = []
    
    #Loop over each renderer in KK_SMRData.json
    for row in json_smr_data:
        #Deselect everything
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = clothes
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action = 'DESELECT')
        
        #Loop over each renderer material and select it
        found_a_material = False
        for mat_name in row['SMRMaterialNames']:
            found_mat_idx = clothes_data.materials.find(mat_name)
            
            if found_mat_idx > -1 and mat_name not in separated_meshes:
                separated_meshes.append(mat_name)
                
                bpy.context.object.active_material_index = found_mat_idx
                bpy.ops.object.material_slot_select()
                found_a_material = True
            
        if not found_a_material:
            continue
        
        #Seperate to a new mesh
        bpy.ops.mesh.separate(type='SELECTED')
        
        #Remove unused materials from the new object and rename it to it's corresponding Renderer name
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.material_slot_remove_unused()
        bpy.context.selected_objects[0].name = row['SMRName']
    bpy.ops.object.select_all(action='DESELECT')
    
    #Pass 2: Clean up
    #Select the Clothes object and remove it's unused material slots
    clothes.select_set(True)
    bpy.ops.object.material_slot_remove_unused()
     
def separate_body(json_smr_data):
    body = bpy.data.objects['Body']
    body_data = body.data
    
    body_obj_material_map = {
        'cf_Ohitomi_L' : 'cf_m_sirome_00',
        'cf_Ohitomi_R' : 'cf_m_sirome_00.001',
        'cf_Ohitomi_L02' : 'cf_m_hitomi_00',
        'cf_Ohitomi_R02' : 'cf_m_hitomi_00.001',
    }
    
    #Pass 1: To make sure each material has a mesh
    #Select the Body object and remove it's unused material slots
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    bpy.ops.object.material_slot_remove_unused()
    
    #Loop over each renderer in KK_SMRData.json
    for row in json_smr_data:
        #Deselect everything
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = body

        if row['SMRName'] not in body_obj_material_map:
            continue
        
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action = 'DESELECT')
        
        #Loop over each renderer material and select it
        found_a_material = False
        for mat_name in row['SMRMaterialNames']:
            found_mat_idx = body_data.materials.find(body_obj_material_map[row['SMRName']])
            
            if found_mat_idx > -1:               
                bpy.context.object.active_material_index = found_mat_idx
                bpy.ops.object.material_slot_select()
                found_a_material = True
            
        if not found_a_material:
            continue
        
        #Seperate to a new mesh
        bpy.ops.mesh.separate(type='SELECTED')
        
        #Remove unused materials from the new object and rename it to it's corresponding Renderer name
        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.ops.object.material_slot_remove_unused()
        bpy.context.selected_objects[0].name = row['SMRName']
    bpy.ops.object.select_all(action='DESELECT')
    
    #Pass 2: Clean up
    #Select the Body object and remove it's unused material slots
    body.select_set(True)
    bpy.ops.object.material_slot_remove_unused()
    bpy.ops.object.select_all(action='DESELECT')
    
     
class separate_meshes(bpy.types.Operator):
    bl_idname = "kkb.separatemeshes"
    bl_label = "Separate Meshes"
    bl_description = "Open the folder containing the KK_SMRData.json file"
    bl_options = {'REGISTER', 'UNDO'}
    
    directory : StringProperty(maxlen=1024, default='', subtype='FILE_PATH', options={'HIDDEN'})
    filter_glob : StringProperty(default='', options={'HIDDEN'})

    def execute(self, context):
        directory = self.directory
        error = checks(directory)
        
        if not error:
            load_smr_data(directory)

        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
   


########## EXPORTER ##########
def export_meshes(directory):
    bpy.ops.object.mode_set(mode = 'OBJECT')
    
    obj_material_map = {
        'cf_Ohitomi_L' : 'cf_m_sirome_00',
        'cf_Ohitomi_R' : 'cf_m_sirome_00',
        'cf_Ohitomi_L02' : 'cf_m_hitomi_00',
        'cf_Ohitomi_R02' : 'cf_m_hitomi_00',
    }

    armature = bpy.data.objects['Armature']
    for obj in bpy.data.objects:
        if obj.parent == armature and obj.visible_get():
            bpy.ops.object.select_all(action='DESELECT')
            
            bpy.context.view_layer.objects.active = armature
            armature.select_set(True)
            obj.select_set(True)
            
            #Special case rename
            if obj.name in obj_material_map:
                obj.data.materials[0].name = obj_material_map[obj.name]
            
            bpy.ops.export_scene.fbx(filepath = directory + obj.name + '.fbx', use_selection = True, use_active_collection = False, global_scale = 1.0, apply_unit_scale = True, apply_scale_options = 'FBX_SCALE_NONE', use_space_transform = True, bake_space_transform = False, object_types={'ARMATURE', 'MESH'}, use_mesh_modifiers = True, use_mesh_modifiers_render = True, mesh_smooth_type  = 'FACE', use_subsurf = False, use_mesh_edges = False, use_tspace = False, use_custom_props = False, add_leaf_bones = False, primary_bone_axis= 'Z', secondary_bone_axis='Y', use_armature_deform_only = False, armature_nodetype = 'NULL', bake_anim = False, bake_anim_use_all_bones = False, bake_anim_use_nla_strips = False, bake_anim_use_all_actions = True, bake_anim_force_startend_keying = True, bake_anim_step = 1.0, bake_anim_simplify_factor = 0, path_mode = 'AUTO', embed_textures = False, batch_mode = 'OFF', use_batch_own_dir = True, axis_forward='-X', axis_up='Z')
                
    bpy.ops.object.select_all(action='DESELECT')
                
                
class export_separate_meshes(bpy.types.Operator, ExportHelper):
    bl_idname = "kkb.exportseparatemeshes"
    bl_label = "Export Separate Meshes"
    bl_description = "Choose where to export meshes"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath : StringProperty(maxlen=1024, default='', subtype='FILE_PATH', options={'HIDDEN'})
    filter_glob : StringProperty(default='', options={'HIDDEN'})

    def execute(self, context):
        filepath = self.filepath
        
        export_meshes(filepath)

        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
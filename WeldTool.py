import bpy
import bgl
import blf
from bpy_extras.view3d_utils import location_3d_to_region_2d
import bmesh

bl_info = {
    "name": "New Weld Tool Test",
    "category": "User",
    "author": "Andreas Strømberg, Moded by CC",
}


def updateHeaderText(context, self):
    if not self.started:
        string = "Select: (LMB), Cancel: (RMB,ESC)"
    else:
        string = "Target Weld: (LMB), Weld At Center: (CTRL+LMB), Add To Selection: (SHIFT+LMB), Connect: (ALT+LMB), Cancel: (RMB,ESC)"
    context.area.header_text_set(string) 

def vertex_active(me):
    bm = bmesh.from_edit_mesh(me)

    for elem in reversed(bm.select_history):
        if isinstance(elem, bmesh.types.BMVert):
            loc = elem.co
            #bm.free()
            return loc
    else:
        return None

def DrawByVertices(mode, verts2d, color, thickness):
    bgl.glColor4f(*color)
    bgl.glEnable(bgl.GL_BLEND)

    if mode is "points":
        bgl.glPointSize(thickness)
        bgl.glBegin(bgl.GL_POINTS)    
    elif mode is "lines":
        bgl.glLineWidth(thickness)
        bgl.glBegin(bgl.GL_LINE_LOOP)

    for x, y in verts2d:
        bgl.glVertex2f(x, y)

    bgl.glEnd()
    bgl.glDisable(bgl.GL_BLEND)
    #restore defaults
    bgl.glLineWidth(1)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

    return

def draw_callback_px(self, context):

    font_id = 0  # XXX, need to find out how best to get this.


   
    # 50% alpha, 2 pixel width line
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(1.0, 0.0, 0.0, 1.0)
    bgl.glLineWidth(2)
    '''
    # draw some text
    blf.position(font_id, 15, 30, 0)
    blf.size(font_id, 20, 72)
    #blf.Color4f(1.0, 0.0, 0.0, 1.0)
    blf.draw(font_id, "Weld Tool")
    '''
    bgl.glBegin(bgl.GL_LINES)
    if self.started and not self.start_vertex == None:
        #print(self.start_vertex)
        verts = [self.start_vertex, self.end_vertex]
        DrawByVertices("lines", verts, self.color, 2)
        #bgl.glVertex2i(self.start_vertex[0], self.start_vertex[1])
        #bgl.glVertex2i(self.end_vertex[0], self.end_vertex[1])

    
    bgl.glEnd()

    v1 = self.end_vertex
    size = 6
    cirVerts = [(v1[0] + size, v1[1]), (v1[0], v1[1] + size), (v1[0] - size, v1[1]), (v1[0], v1[1] - size)]
    DrawByVertices("lines", cirVerts, [1, 1, 1, 1], 3)

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
    


def main(context, event, started):
    """Run this function on left mouse, execute the ray cast"""
    coord = event.mouse_region_x, event.mouse_region_y

    if started:
        result = bpy.ops.view3d.select(extend=True, location=coord)
    else:
        result = bpy.ops.view3d.select(extend=False, location=coord)

    if result == {'PASS_THROUGH'}:
        print('pass')
        bpy.ops.mesh.select_all(action='DESELECT')


class WeldTool(bpy.types.Operator):
    
    bl_idname = "mesh.weld_tool"
    bl_label = "Weld Tool Operator"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.started = None
        self.start_vertex = None
        self.end_vertex = None
        self.end_vertexloc = None
        self._handle = None
        self.down = None
        self.prev_selectmode = None
        self.color = (1, 1, 1, 1)

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.ctrl:
            self.color = (1, 0, 0, 1)
        elif event.alt:
            self.color = (0, 0, 1, 1)
        elif event.shift:
            self.color = (0, 1, 0, 1)
        else:
            self.color = (1, 1, 1, 1)
        
        if not self.end_vertexloc == None:
            self.start_vertex = location_3d_to_region_2d(context.region, context.space_data.region_3d, self.end_vertexloc)
        self.end_vertex = (event.mouse_region_x, event.mouse_region_y)
        
        if not bpy.context.scene.tool_settings.mesh_select_mode[:] == (True, False, False):
            bpy.ops.mesh.select_mode(type="VERT")
        
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE', 'Z'}:
            # allow navigation
            
            return {'PASS_THROUGH'}
        #elif event.type == 'MOUSEMOVE':
            #if self.started:
            
            
            
            

        elif event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
            #main(context, event, self.started)
            
            #if not self.down:
                main(context, event, self.started)
                if not context.object.data.total_vert_sel > 0:
                    self.started = False
                    updateHeaderText(context, self)
            
            if event.shift and context.object.data.total_vert_sel > 0:
                self.end_vertexloc =  context.object.matrix_world * vertex_active(bpy.context.active_object.data)
                return {'RUNNING_MODAL'}
            
            if not self.started:
                if context.object.data.total_vert_sel == 1:
                    self.start_vertex = (event.mouse_region_x, event.mouse_region_y)
                    
                    #bm = bmesh.from_edit_mesh(bpy.context.active_object)
                    #vertex_active(bpy.context.active_object)
                    
                    self.end_vertexloc =  context.object.matrix_world * vertex_active(bpy.context.active_object.data)
                    self.started = True
                    updateHeaderText(context, self)
            elif context.object.data.total_vert_sel > 1:
                #print(context.object.data.total_vert_sel == 2)
                if event.ctrl:
                    bpy.ops.mesh.merge(type='CENTER')
                    #self.color = (1, 0, 0, 1)
                elif event.alt:
                    bpy.ops.mesh.vert_connect_path()
                    #bpy.ops.mesh.merge(type='LAST')
                    #self.color = (0, 0, 1, 1)
                else:
                    bpy.ops.mesh.merge(type='LAST')
                    #bpy.ops.mesh.vert_connect_path()
                    #self.color = (1, 1, 1, 1)
                    
                bpy.ops.ed.undo_push(message="Add an undo step *function may be moved*")
                bpy.ops.mesh.select_all(action='DESELECT')
                self.started = False
                updateHeaderText(context, self)
            
            '''
            if self.mode == 0:
                main(context, event, self.started)
                self.mode = self.mode + 1
            elif self.mode == 1:
                
                self.mode = self.mode + 1
            if self.mode == 2:
                
                self.mode = 0
            '''
            #self.down = not self.down
            return {'RUNNING_MODAL'}
        elif event.type in {'RIGHTMOUSE', 'ESC', 'TAB'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            if event.type == 'TAB':
                bpy.ops.object.editmode_toggle()
            #print(self.prev_selectmode[0], self.prev_selectmode[1], self.prev_selectmode[2])
            if not bpy.context.scene.tool_settings.mesh_select_mode[:] == self.prev_selectmode:
            #    self.report({'INFO'}, 'selectmode')
                print('dsfsdfsd')
                bpy.context.tool_settings.mesh_select_mode = self.prev_selectmode
                #bpy.ops.mesh.select_mode(self.prev_selectmode)
            bpy.context.window.cursor_set("CROSSHAIR")
            context.area.header_text_set()
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.space_data.type == 'VIEW_3D' and context.object.mode == 'EDIT':
            args = (self, context)

            self.start_vertex = (0, 0)
            self.end_vertex = (0, 0)

            context.window_manager.modal_handler_add(self)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

            self.started = False
            self.down = False
            #if not tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (True, False, False):
            self.prev_selectmode = bpy.context.scene.tool_settings.mesh_select_mode[:]
            #print(self.prev_selectmode[0], self.prev_selectmode[1], self.prev_selectmode[2])
            bpy.ops.mesh.select_mode(type="VERT")
            #print(self.prev_selectmode[0], self.prev_selectmode[1], self.prev_selectmode[2])
            bpy.context.window.cursor_set("NONE")
            updateHeaderText(context, self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d, and object mode must be edit")
            return {'CANCELLED'}


#Add Buttons to the Tool panel
class ModalAddPanel(bpy.types.Panel):
    """Creates a Panel in the Toolbar"""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Tools'
    bl_label = "Mesh Tools"


    def draw(self, context):
        lay_out = self.layout.column(align=True)
        lay_out.operator(operator="mesh.weld_tool", text="Weld Tool", icon='STICKY_UVS_VERT')



def register():
    bpy.utils.register_class(WeldTool)
    bpy.utils.register_class(ModalAddPanel)

def unregister():
    bpy.utils.unregister_class(WeldTool)
    bpy.utils.unregister_class(ModalAddPanel)

if __name__ == "__main__":
    register()
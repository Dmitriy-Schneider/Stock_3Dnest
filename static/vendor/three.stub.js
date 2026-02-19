// Минимальная заглушка Three.js, чтобы UI не падал без CDN
class Color { constructor(){} setHSL(){ return this; } getHex(){ return 0x888888; } }
class Scene { constructor(){ this.background=null; } add(){ } remove(){} }
class PerspectiveCamera { constructor(){ this.position={set(){}}; } }
class WebGLRenderer { constructor(){ this.domElement=document.createElement('div'); } setSize(){ } render(){ } }
class BoxGeometry { constructor(){} }
class MeshPhysicalMaterial { constructor(opts){ this.transparent=!!opts?.transparent; this.opacity=opts?.opacity ?? 1; } }
class Mesh { constructor(){ this.material=new MeshPhysicalMaterial({}); this.position={ set: function(){} }; this.add = function(){} } }
class HemisphereLight { constructor(){ this.position = { set(){} }; } }
class DirectionalLight { constructor(){ this.position = { set(){} }; } }
class GridHelper { constructor(){ this.rotation={x:0}; this.visible=false; } }
class EdgesGeometry { constructor(){} }
class WireframeGeometry { constructor(){} }
class LineBasicMaterial { constructor(){} }
class LineSegments { constructor(){} }

export default {
  __isStub: true,
  Color, Scene, PerspectiveCamera, WebGLRenderer, BoxGeometry, MeshPhysicalMaterial, Mesh,
  HemisphereLight, DirectionalLight, GridHelper, EdgesGeometry, WireframeGeometry, LineBasicMaterial, LineSegments,
};

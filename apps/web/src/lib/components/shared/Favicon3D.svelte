<script lang="ts">
  /**
   * Favicon3D - Animated 3D favicon (inspired by Beatcatalogue Logo3D).
   * 
   * Features:
   * - Three.js WebGL animation with wave distortion
   * - Chromatic aberration
   * - Mouse tracking
   * - Auto rotation
   * - Fallback for mobile/WebGL failure
   */
  import { onMount } from "svelte";
  import { browser } from "$app/environment";
  
  export let size: number = 200;
  
  let container: HTMLDivElement;
  let mouseX = 0;
  let mouseY = 0;
  let isMobile = false;
  let webglFailed = false;
  
  const FAVICON_URL = "/favicon.svg";
  
  onMount(async () => {
    if (!browser) return;
    
    // Detectar móvil
    isMobile = window.innerWidth < 768 || 
               /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               ('ontouchstart' in window);
    
    // En móvil, usar fallback CSS simple
    if (isMobile) {
      return;
    }
    
    // WebGL solo en desktop
    try {
      const THREE = await import("three");
      
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
      camera.position.z = 120;
      
      const renderer = new THREE.WebGLRenderer({
        alpha: true,
        antialias: true,
        powerPreference: "high-performance"
      });
      renderer.setSize(size, size);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      container.appendChild(renderer.domElement);
      
      // Luces con colores Kidyland
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
      scene.add(ambientLight);
      
      const pointLight = new THREE.PointLight(0x0093f7, 1.5); // Kidyland blue
      pointLight.position.set(0, 0, 50);
      scene.add(pointLight);
      
      const greenLight = new THREE.PointLight(0x3dad09, 0.8); // Kidyland green
      greenLight.position.set(30, 30, 30);
      scene.add(greenLight);
      
      const material = new THREE.ShaderMaterial({
        uniforms: {
          uTexture: { value: null },
          uTime: { value: 0 },
          uMouse: { value: new THREE.Vector2(0, 0) },
          uDepth: { value: 35.0 },
          uIntensity: { value: 0.02 }
        },
        vertexShader: `
          uniform sampler2D uTexture;
          uniform float uDepth;
          uniform float uTime;
          uniform vec2 uMouse;
          varying vec2 vUv;
          varying float vDisplacement;
          
          void main() {
            vUv = uv;
            
            vec4 texColor = texture2D(uTexture, uv);
            float displacement = texColor.a * uDepth;
            
            // Wave distortion
            displacement += sin(uv.y * 15.0 + uTime * 1.5) * 1.0;
            displacement += cos(uv.x * 10.0 + uTime * 0.8) * 0.5;
            
            // Mouse interaction
            displacement += length(uMouse) * 5.0 * texColor.a;
            
            vDisplacement = displacement;
            
            vec3 newPosition = position;
            newPosition.z += displacement;
            
            gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
          }
        `,
        fragmentShader: `
          uniform sampler2D uTexture;
          uniform float uTime;
          uniform vec2 uMouse;
          uniform float uIntensity;
          varying vec2 vUv;
          varying float vDisplacement;
          
          float random(vec2 st) {
            return fract(sin(dot(st.xy, vec2(127.1,78.233))) * 43758.5453123);
          }
          
          void main() {
            vec2 uv = vUv;
            
            // Wave distortion
            float wave = sin(uv.y * 20.0 + uTime * 2.0) * 0.005;
            uv.x += wave;
            
            // Chromatic aberration
            float aberration = uIntensity + length(uMouse) * 0.01;
            vec2 uvR = uv + vec2(aberration, 0.0);
            vec2 uvG = uv;
            vec2 uvB = uv - vec2(aberration, 0.0);
            
            float r = texture2D(uTexture, uvR).r;
            float g = texture2D(uTexture, uvG).g;
            float b = texture2D(uTexture, uvB).b;
            float a = texture2D(uTexture, uv).a;
            
            // Glitch aleatorio
            float glitch = step(0.98, random(vec2(uTime * 0.1, uv.y)));
            uv.x += glitch * 0.05;
            
            // Film grain
            float noise = random(uv + uTime * 0.5) * 0.05;
            
            // Iluminación basada en profundidad
            float lighting = vDisplacement / 35.0;
            vec3 color = vec3(r, g, b) * (0.85 + lighting * 0.3) + noise;
            
            gl_FragColor = vec4(color, a);
          }
        `,
        transparent: true,
        side: THREE.DoubleSide
      });
      
      const geometry = new THREE.PlaneGeometry(70, 70, 256, 256);
      const mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);
      
      // Load texture
      new THREE.TextureLoader().load(FAVICON_URL, (texture) => {
        material.uniforms.uTexture.value = texture;
      });
      
      // Mouse tracking
      const onMouseMove = (e: MouseEvent) => {
        const rect = container.getBoundingClientRect();
        mouseX = ((e.clientX - rect.left) / rect.width - 0.5) * 2;
        mouseY = ((e.clientY - rect.top) / rect.height - 0.5) * -2;
      };
      
      container.addEventListener("mousemove", onMouseMove);
      
      // Animation loop
      let time = 0;
      function animate() {
        requestAnimationFrame(animate);
        time += 0.016;
        
        material.uniforms.uTime.value = time;
        material.uniforms.uMouse.value.set(mouseX, mouseY);
        
        // Rotation based on mouse + auto rotation
        mesh.rotation.y = mouseX * 0.5 + Math.sin(time * 0.4) * 0.15;
        mesh.rotation.x = -mouseY * 0.5 + Math.cos(time * 0.25) * 0.15;
        
        // Move lights with mouse
        pointLight.position.x = mouseX * 40;
        pointLight.position.y = mouseY * 40;
        
        renderer.render(scene, camera);
      }
      animate();
      
      // Cleanup
      return () => {
        container.removeEventListener("mousemove", onMouseMove);
        renderer.dispose();
        if (container && container.contains(renderer.domElement)) {
          container.removeChild(renderer.domElement);
        }
      };
    } catch (error) {
      console.warn("Favicon3D WebGL failed:", error);
      webglFailed = true;
    }
  });
</script>

{#if isMobile || webglFailed}
  <!-- Fallback CSS para móvil/WebGL fallido -->
  <div class="favicon-fallback" style="width: {size}px; height: {size}px;">
    <img 
      src={FAVICON_URL} 
      alt="Kidyland Mascot"
      class="favicon-image"
    />
  </div>
{:else}
  <!-- WebGL 3D version para desktop -->
  <div bind:this={container} class="favicon-3d-container" style="width: {size}px; height: {size}px;"></div>
{/if}

<style>
  .favicon-fallback {
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    animation: float 3s ease-in-out infinite;
  }
  
  .favicon-image {
    width: 100%;
    height: 100%;
    object-fit: contain;
    filter: drop-shadow(0 0 20px rgba(0, 147, 247, 0.6));
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .favicon-fallback:hover .favicon-image {
    transform: scale(1.1) rotate(5deg);
    filter: 
      drop-shadow(0 0 30px rgba(0, 147, 247, 0.8))
      drop-shadow(0 0 40px rgba(61, 173, 9, 0.5));
  }
  
  .favicon-3d-container {
    cursor: pointer;
  }
  
  @keyframes float {
    0%, 100% {
      transform: translateY(0);
    }
    50% {
      transform: translateY(-10px);
    }
  }
  
  /* Responsive */
  @media (max-width: 640px) {
    .favicon-image {
      filter: drop-shadow(0 0 15px rgba(0, 147, 247, 0.5));
    }
  }
</style>




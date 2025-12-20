<script lang="ts">
  /**
   * WaveBackground - Animated wave background (inspired by Beatcatalogue).
   * 
   * Features:
   * - Three.js WebGL with wave distortion
   * - Mouse tracking
   * - Scroll interaction
   * - Kidyland colors (cyan/magenta → blue/green)
   * - Performance optimized
   */
  import { onMount } from "svelte";
  import { browser } from "$app/environment";
  
  let container: HTMLDivElement;
  let scrollY = 0;
  let mouseX = 0;
  let mouseY = 0;
  let webglSupported = true;
  
  onMount(async () => {
    if (!browser) return;
    
    const isMobile = window.innerWidth < 768 || 
                     /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    try {
      const THREE = await import("three");
      
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(
        75,
        window.innerWidth / window.innerHeight,
        0.1,
        1000
      );
      camera.position.z = 30;
      
      const renderer = new THREE.WebGLRenderer({ 
        alpha: true, 
        antialias: !isMobile,
        powerPreference: isMobile ? "low-power" : "high-performance"
      });
      renderer.setSize(window.innerWidth, window.innerHeight);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, isMobile ? 1 : 2));
      container.appendChild(renderer.domElement);
      
      const material = new THREE.ShaderMaterial({
        uniforms: {
          uTime: { value: 0 },
          uScroll: { value: 0 },
          uMouse: { value: new THREE.Vector2(0, 0) },
          uOpacity: { value: isMobile ? 0.15 : 0.3 }
        },
        vertexShader: `
          uniform float uScroll;
          uniform vec2 uMouse;
          varying vec2 vUv;
          varying float vElevation;
          
          void main() {
            vUv = uv;
            vec3 pos = position;
            
            // Wave distortions
            float lateralWave = sin(pos.x * 0.15 + uScroll * 0.3);
            float verticalWave = cos(pos.y * 0.12 - uScroll * 0.2);
            float diagonal = sin((pos.x + pos.y) * 0.1 + uScroll * 0.25);
            
            // Mouse interaction
            float distanceFromMouse = length(vec2(pos.x, pos.y) - uMouse * 50.0);
            float mouseWave = sin(distanceFromMouse * 0.15) * 9.0 / (distanceFromMouse + 1.0);
            
            pos.x += uMouse.x * 3.0 + uScroll * 3.0;
            pos.y += uMouse.y * 3.0;
            
            pos.z -= lateralWave * 7.0 + verticalWave * 5.0 + diagonal * 4.0 + mouseWave;
            vElevation = pos.z;
            
            gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
          }
        `,
        fragmentShader: `
          uniform float uTime;
          uniform float uOpacity;
          varying vec2 vUv;
          varying float vElevation;
          
          float hash(vec2 p) {
            return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
          }
          
          vec2 hash2(vec2 p) {
            return vec2(
              fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453),
              fract(sin(dot(p, vec2(269.5, 183.3))) * 43758.5453)
            );
          }
          
          void main() {
            // Kidyland colors (blue/green instead of cyan/magenta)
            vec3 color1 = vec3(0.0, 0.58, 0.97); // #0093F7
            vec3 color2 = vec3(0.24, 0.68, 0.04); // #3DAD09
            
            float mixer = (-vElevation + 20.0) / 40.0;
            vec3 color = mix(color1, color2, mixer);
            
            vec2 center = vec2(0.5, 0.5);
            vec2 toCenter = vUv - center;
            float distFromCenter = length(toCenter);
            float angle = atan(toCenter.y, toCenter.x);
            
            float rings = ${isMobile ? '6.0' : '10.0'};
            float ringRadius = distFromCenter * rings;
            float ringIndex = floor(ringRadius);
            float ringPos = fract(ringRadius);
            
            float pointsInRing = 6.0 + ringIndex * 3.5;
            float angleStep = 6.28318 / pointsInRing;
            float angleIndex = floor(angle / angleStep);
            float anglePos = fract(angle / angleStep);
            
            vec2 pointId = vec2(ringIndex, angleIndex);
            
            float blob = 0.0;
            
            for(float i = 0.0; i < ${isMobile ? '1.0' : '2.0'}; i++) {
              vec2 randomSplatter = hash2(pointId + i * 50.0) - 0.5;
              randomSplatter *= 0.6;
              
              vec2 pointCenter = vec2(ringPos - 0.5, anglePos - 0.5) + randomSplatter;
              
              float offset = hash(pointId + i * 100.0) * 6.28;
              float radius = 0.18 + sin(uTime * 0.5 + offset) * 0.07;
              
              float aspectRatio = ringRadius / (ringIndex + 1.0);
              pointCenter.y *= aspectRatio * (0.8 + hash(pointId) * 0.4);
              
              float dist = length(pointCenter);
              float point = smoothstep(radius, 0.0, dist);
              blob += point * 0.28;
            }
            
            float edgeFade = smoothstep(0.0, 0.2, distFromCenter) * smoothstep(0.9, 0.6, distFromCenter);
            
            gl_FragColor = vec4(color, blob * edgeFade * uOpacity);
          }
        `,
        transparent: true,
        side: THREE.DoubleSide
      });
      
      const geometry = new THREE.PlaneGeometry(120, 120, isMobile ? 50 : 100, isMobile ? 50 : 100);
      const mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);
      
      const handleScroll = () => {
        scrollY = window.scrollY * 0.002;
      };
      
      const handleMouseMove = (e: MouseEvent) => {
        mouseX = (e.clientX / window.innerWidth) * 2 - 1;
        mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
      };
      
      window.addEventListener("scroll", handleScroll, { passive: true });
      if (!isMobile) {
        window.addEventListener("mousemove", handleMouseMove);
      }
      
      let time = 0;
      function animate() {
        requestAnimationFrame(animate);
        time += 0.005;
        
        material.uniforms.uTime.value = time;
        material.uniforms.uScroll.value += (scrollY - material.uniforms.uScroll.value) * 0.08;
        if (!isMobile) {
          material.uniforms.uMouse.value.x += (mouseX - material.uniforms.uMouse.value.x) * 0.15;
          material.uniforms.uMouse.value.y += (mouseY - material.uniforms.uMouse.value.y) * 0.15;
        }
        
        renderer.render(scene, camera);
      }
      animate();
      
      const handleResize = () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
      };
      
      window.addEventListener("resize", handleResize);
      
      return () => {
        window.removeEventListener("scroll", handleScroll);
        if (!isMobile) {
          window.removeEventListener("mousemove", handleMouseMove);
        }
        window.removeEventListener("resize", handleResize);
        renderer.dispose();
        if (container && renderer.domElement) {
          container.removeChild(renderer.domElement);
        }
      };
      
    } catch (error) {
      console.warn("WebGL failed, using CSS fallback:", error);
      webglSupported = false;
    }
  });
</script>

<div bind:this={container} class="wave-background">
  {#if !webglSupported}
    <!-- Fallback CSS si WebGL falla -->
    <div class="wave-fallback"></div>
  {/if}
</div>

<style>
  .wave-background {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: -10;
    filter: blur(1px);
  }
  
  .wave-fallback {
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, #0093f7 0%, #3dad09 100%);
  }
</style>


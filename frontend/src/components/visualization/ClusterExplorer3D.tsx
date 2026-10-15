import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import { useApp } from '../../lib/store';
import { api } from '../../lib/api';
import type { Point3D, Embeddings3DResponse } from '../../lib/types';
import { RotateCw, Sparkles } from 'lucide-react';

interface ClusterExplorer3DProps {
  runId: string;
  datasetId: string;
}

const CLASS_PALETTE = [
  '#6366f1', // indigo
  '#10b981', // emerald
  '#0ea5e9', // sky
  '#f59e0b', // amber
  '#ec4899', // pink
  '#8b5cf6', // purple
  '#14b8a6', // teal
  '#f97316', // orange
];

export const ClusterExplorer3D: React.FC<ClusterExplorer3DProps> = ({
  runId,
  datasetId,
}) => {
  const { password } = useApp();
  const mountRef = useRef<HTMLDivElement>(null);

  const [data, setData] = useState<Embeddings3DResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [hoveredPoint, setHoveredPoint] = useState<Point3D | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);
  const [filterMode, setFilterMode] = useState<'all' | 'outliers_only' | 'inliers_only'>('all');
  const [autoRotate, setAutoRotate] = useState<boolean>(true);

  // Load 3D coordinates
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getEmbeddings3D(runId, password);
      setData(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load 3D embedding coordinates');
    } finally {
      setLoading(false);
    }
  }, [runId, password]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Three.js Scene Setup & Loop
  useEffect(() => {
    if (!mountRef.current || !data || data.points.length === 0) return;

    const container = mountRef.current;
    const width = container.clientWidth || 600;
    const height = container.clientHeight || 450;

    // Scene & Camera
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x09090b); // zinc-950

    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
    camera.position.set(0, 5, 18);
    camera.lookAt(0, 0, 0);

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // Ambient & Directional Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x6366f1, 2.5, 50);
    pointLight.position.set(10, 15, 10);
    scene.add(pointLight);

    // Coordinate Grid & Wireframe Orbit Ring
    const gridHelper = new THREE.GridHelper(16, 16, 0x27272a, 0x18181b);
    gridHelper.position.y = -4;
    scene.add(gridHelper);

    // Collect Unique Classes for Color Mapping
    const uniqueClasses = Array.from(new Set(data.points.map(p => p.ground_truth_class))).sort();
    const classColorMap = new Map<string, THREE.Color>();
    uniqueClasses.forEach((cls, i) => {
      classColorMap.set(cls, new THREE.Color(CLASS_PALETTE[i % CLASS_PALETTE.length]));
    });

    // Mesh Group for Interactivity
    const pointGroup = new THREE.Group();
    scene.add(pointGroup);

    // Create interactive sphere meshes
    const meshes: { mesh: THREE.Mesh; point: Point3D }[] = [];
    const sphereGeo = new THREE.SphereGeometry(0.24, 16, 16);
    const outlierGeo = new THREE.SphereGeometry(0.38, 16, 16);

    const visiblePoints = data.points.filter(p => {
      if (filterMode === 'outliers_only') return p.is_outlier;
      if (filterMode === 'inliers_only') return !p.is_outlier;
      return true;
    });

    visiblePoints.forEach(p => {
      const color = p.is_outlier ? new THREE.Color(0xf43f5e) : (classColorMap.get(p.ground_truth_class) || new THREE.Color(0x6366f1));
      const mat = new THREE.MeshStandardMaterial({
        color,
        roughness: 0.3,
        metalness: 0.2,
        emissive: p.is_outlier ? new THREE.Color(0x881337) : new THREE.Color(0x000000),
        emissiveIntensity: p.is_outlier ? 0.8 : 0,
      });

      const mesh = new THREE.Mesh(p.is_outlier ? outlierGeo : sphereGeo, mat);
      mesh.position.set(p.x, p.y, p.z);
      pointGroup.add(mesh);
      meshes.push({ mesh, point: p });

      // Outlier pulsing wireframe halo
      if (p.is_outlier) {
        const haloGeo = new THREE.RingGeometry(0.45, 0.58, 24);
        const haloMat = new THREE.MeshBasicMaterial({
          color: 0xf43f5e,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.7,
        });
        const halo = new THREE.Mesh(haloGeo, haloMat);
        halo.position.set(p.x, p.y, p.z);
        halo.lookAt(camera.position);
        pointGroup.add(halo);
      }
    });

    // Orbit Drag Interaction State
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let rotationSpeedX = 0;
    let rotationSpeedY = 0;

    const onMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const onMouseMove = (e: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      const mouseX = ((e.clientX - rect.left) / width) * 2 - 1;
      const mouseY = -((e.clientY - rect.top) / height) * 2 + 1;

      if (isDragging) {
        const deltaX = e.clientX - prevMouseX;
        const deltaY = e.clientY - prevMouseY;
        pointGroup.rotation.y += deltaX * 0.008;
        pointGroup.rotation.x += deltaY * 0.008;
        rotationSpeedX = deltaY * 0.002;
        rotationSpeedY = deltaX * 0.002;
        prevMouseX = e.clientX;
        prevMouseY = e.clientY;
      } else {
        // Raycast for hover tooltip
        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(new THREE.Vector2(mouseX, mouseY), camera);
        const intersects = raycaster.intersectObjects(meshes.map(m => m.mesh));

        if (intersects.length > 0) {
          const hit = meshes.find(m => m.mesh === intersects[0].object);
          if (hit) {
            setHoveredPoint(hit.point);
            setTooltipPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
          }
        } else {
          setHoveredPoint(null);
          setTooltipPos(null);
        }
      }
    };

    const onMouseUp = () => {
      isDragging = false;
    };

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      camera.position.z = Math.min(Math.max(camera.position.z + e.deltaY * 0.02, 6), 35);
    };

    const domElement = renderer.domElement;
    domElement.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    domElement.addEventListener('wheel', onWheel, { passive: false });

    // Animation Loop
    let animId: number;
    const animate = () => {
      animId = requestAnimationFrame(animate);

      if (autoRotate && !isDragging) {
        pointGroup.rotation.y += 0.0025;
      }

      // Smooth inertia
      if (!isDragging && (Math.abs(rotationSpeedX) > 0.0001 || Math.abs(rotationSpeedY) > 0.0001)) {
        pointGroup.rotation.x += rotationSpeedX;
        pointGroup.rotation.y += rotationSpeedY;
        rotationSpeedX *= 0.94;
        rotationSpeedY *= 0.94;
      }

      renderer.render(scene, camera);
    };
    animate();

    // Resize Handler
    const handleResize = () => {
      if (!container) return;
      const newW = container.clientWidth;
      const newH = container.clientHeight;
      camera.aspect = newW / newH;
      camera.updateProjectionMatrix();
      renderer.setSize(newW, newH);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animId);
      domElement.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      domElement.removeEventListener('wheel', onWheel);
      window.removeEventListener('resize', handleResize);
      renderer.dispose();
      sphereGeo.dispose();
      outlierGeo.dispose();
    };
  }, [data, filterMode, autoRotate]);

  if (loading) {
    return (
      <div className="h-96 w-full rounded-2xl glass-panel flex flex-col items-center justify-center gap-3 animate-pulse">
        <RotateCw className="w-8 h-8 text-indigo-400 animate-spin" />
        <span className="text-xs text-zinc-400 font-mono">
          Generating 3D PCA embedding manifold...
        </span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="h-96 w-full rounded-2xl glass-panel border border-rose-500/20 p-8 flex flex-col items-center justify-center text-center">
        <span className="text-sm text-rose-400 font-semibold mb-2">3D Manifold Unavailable</span>
        <span className="text-xs text-zinc-500 max-w-sm mb-4">{error}</span>
        <button
          onClick={loadData}
          className="px-3 py-1.5 rounded-lg bg-zinc-800 text-xs text-zinc-300 hover:text-white"
        >
          Retry
        </button>
      </div>
    );
  }

  const uniqueClasses = Array.from(new Set(data.points.map(p => p.ground_truth_class))).sort();
  const outlierCount = data.points.filter(p => p.is_outlier).length;

  return (
    <div className="relative w-full rounded-2xl glass-panel border border-zinc-800 overflow-hidden shadow-2xl">
      {/* Visualizer Top Bar Telemetry */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 border-b border-zinc-800/80 bg-zinc-950/70">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <h4 className="text-xs font-semibold text-zinc-200 font-sans">
            Interactive 3D Embedding & Outlier Space
          </h4>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400 font-mono">
            {data.sample_count} points
          </span>
          {data.has_real_embeddings ? (
            <span className="text-[10px] text-emerald-400 font-mono bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
              ResNet-18 PCA (PC1: {(data.variance_explained[0] * 100).toFixed(0)}%, PC2: {(data.variance_explained[1] * 100).toFixed(0)}%)
            </span>
          ) : (
            <span className="text-[10px] text-sky-400 font-mono bg-sky-500/10 px-2 py-0.5 rounded-full border border-sky-500/20">
              Geometric Metric Projection
            </span>
          )}
        </div>

        {/* View Controls */}
        <div className="flex items-center gap-2 text-xs">
          <div className="flex items-center rounded-lg bg-zinc-900 border border-zinc-800 p-0.5">
            <button
              onClick={() => setFilterMode('all')}
              className={`px-2 py-1 rounded text-[11px] font-medium transition-colors ${
                filterMode === 'all' ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              All ({data.sample_count})
            </button>
            <button
              onClick={() => setFilterMode('outliers_only')}
              className={`px-2 py-1 rounded text-[11px] font-medium transition-colors flex items-center gap-1 ${
                filterMode === 'outliers_only' ? 'bg-rose-500/20 text-rose-300 font-semibold' : 'text-zinc-400 hover:text-rose-400'
              }`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
              Outliers ({outlierCount})
            </button>
            <button
              onClick={() => setFilterMode('inliers_only')}
              className={`px-2 py-1 rounded text-[11px] font-medium transition-colors ${
                filterMode === 'inliers_only' ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              Inliers
            </button>
          </div>

          <button
            onClick={() => setAutoRotate(prev => !prev)}
            className={`p-1.5 rounded-lg border text-xs transition-colors ${
              autoRotate
                ? 'bg-indigo-600/20 border-indigo-500/40 text-indigo-300'
                : 'bg-zinc-900 border-zinc-800 text-zinc-400'
            }`}
            title="Toggle 3D auto rotation"
          >
            <RotateCw className={`w-3.5 h-3.5 ${autoRotate ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* 3D WebGL Canvas Container */}
      <div
        ref={mountRef}
        className="w-full h-[440px] cursor-grab active:cursor-grabbing relative overflow-hidden bg-zinc-950"
      />

      {/* Floating Hover Tooltip */}
      {hoveredPoint && tooltipPos && (
        <div
          className="absolute pointer-events-none z-30 p-3 rounded-xl glass-panel border border-zinc-700 bg-zinc-900/95 shadow-2xl text-xs max-w-xs transition-transform"
          style={{
            left: Math.min(tooltipPos.x + 15, 450),
            top: Math.max(tooltipPos.y - 120, 15),
          }}
        >
          <div className="flex items-start gap-2.5">
            <img
              src={api.getSampleImageUrl(datasetId, hoveredPoint.sample_ref, password)}
              alt="Thumbnail"
              className="w-12 h-12 rounded-lg object-cover bg-zinc-800 border border-zinc-700 shrink-0"
              onError={e => {
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
            <div className="min-w-0">
              <div className="font-mono text-zinc-200 truncate font-semibold">
                {hoveredPoint.sample_ref}
              </div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="text-zinc-400">Class:</span>
                <span className="font-medium text-white px-1.5 py-0.2 rounded bg-zinc-800">
                  {hoveredPoint.ground_truth_class}
                </span>
              </div>
              <div className="text-[11px] text-zinc-400 mt-0.5">
                Split: <span className="text-zinc-300 font-mono">{hoveredPoint.split}</span> | Cluster: #{hoveredPoint.cluster_id}
              </div>
              {hoveredPoint.is_outlier && (
                <div className="mt-1 px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 text-[10px] font-semibold border border-rose-500/30">
                  Isolation Forest Outlier (Score: {hoveredPoint.outlier_score})
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Interactive Legend & Hint */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 border-t border-zinc-800/80 bg-zinc-950/80 text-[11px]">
        <div className="flex items-center gap-3 overflow-x-auto py-0.5">
          <span className="text-zinc-500 font-mono">Classes:</span>
          {uniqueClasses.map((cls, i) => (
            <div key={cls} className="flex items-center gap-1.5">
              <span
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: CLASS_PALETTE[i % CLASS_PALETTE.length] }}
              />
              <span className="text-zinc-300">{cls}</span>
            </div>
          ))}
          <div className="flex items-center gap-1.5 ml-2">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
            <span className="text-rose-400 font-medium">Outlier Halo</span>
          </div>
        </div>

        <div className="text-[11px] text-zinc-500 font-mono hidden sm:block">
          Click & Drag to rotate • Scroll to zoom • Hover sample to inspect
        </div>
      </div>
    </div>
  );
};

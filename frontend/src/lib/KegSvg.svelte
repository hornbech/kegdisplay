<script>
  export let color = '#C8860A';
  export let status = 'empty';   // empty | fermenting | conditioning | on_tap | archived
  export let slot = 0;           // unique clipPath ids across all 8 kegs
  export let size = 80;          // width in px; height scales 1.6x
  export let fill = null;        // optional 0..1 override; falls back to status map

  // Status → decorative fill (0..1) when no explicit fill supplied
  const fillMap = { empty: 0, fermenting: 0.92, conditioning: 0.95, on_tap: 0.55, archived: 0.08 };
  $: fillLevel = fill != null ? fill : (fillMap[status] ?? 0);

  $: W = size;
  $: H = size * 1.6;
  $: bodyW = W * 0.72;
  $: bodyH = H * 0.68;
  $: bodyX = (W - bodyW) / 2;
  $: bodyY = H * 0.16;
  $: fillH = bodyH * fillLevel;
  $: fillY = bodyY + bodyH - fillH;

  $: isEmpty = status === 'empty';
  $: opacity = status === 'archived' ? 0.4 : 1;

  $: clipId = `keg-clip-${slot}`;
  $: bodyGrad = `keg-body-${slot}`;
  $: liquidGrad = `keg-liquid-${slot}`;
  $: brassGrad = `keg-brass-${slot}`;
</script>

<svg width={W} height={H} viewBox="0 0 {W} {H}" style="opacity:{opacity}">
  <defs>
    <clipPath id={clipId}>
      <rect x={bodyX} y={fillY} width={bodyW} height={fillH} rx="10" />
    </clipPath>
    <linearGradient id={bodyGrad} x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#1a1613" />
      <stop offset="0.5" stop-color="#2a2420" />
      <stop offset="1" stop-color="#0f0c0a" />
    </linearGradient>
    <linearGradient id={liquidGrad} x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color={color} stop-opacity="0.75" />
      <stop offset="0.4" stop-color={color} stop-opacity="1" />
      <stop offset="1" stop-color={color} stop-opacity="0.6" />
    </linearGradient>
    <linearGradient id={brassGrad} x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#c8860a" />
      <stop offset="0.5" stop-color="#e8a020" />
      <stop offset="1" stop-color="#8a5a05" />
    </linearGradient>
  </defs>

  <!-- Handles -->
  <path d="M{bodyX - 4},{bodyY + bodyH * 0.18} Q{bodyX - 16},{bodyY + bodyH * 0.34} {bodyX - 4},{bodyY + bodyH * 0.5}"
        fill="none" stroke="#3a3228" stroke-width="6" stroke-linecap="round" />
  <path d="M{bodyX + bodyW + 4},{bodyY + bodyH * 0.18} Q{bodyX + bodyW + 16},{bodyY + bodyH * 0.34} {bodyX + bodyW + 4},{bodyY + bodyH * 0.5}"
        fill="none" stroke="#3a3228" stroke-width="6" stroke-linecap="round" />

  <!-- Body -->
  <rect x={bodyX} y={bodyY} width={bodyW} height={bodyH} rx="10"
        fill="url(#{bodyGrad})" stroke="#4a3d2e" stroke-width="1.5" />

  <!-- Liquid fill -->
  {#if fillLevel > 0}
    <rect x={bodyX} y={bodyY} width={bodyW} height={bodyH} rx="10"
          fill="url(#{liquidGrad})" clip-path="url(#{clipId})"
          style="transition: all 0.6s ease" />
    <!-- Surface highlight -->
    <ellipse cx={W / 2} cy={fillY} rx={bodyW / 2 - 4} ry="3"
             fill={color} opacity="0.5" />
    <ellipse cx={W / 2} cy={fillY + 1} rx={bodyW / 2 - 8} ry="1.5"
             fill="rgba(255,255,255,0.3)" />
    <!-- Vertical shine -->
    <rect x={bodyX + 8} y={fillY + 6} width="5" height={Math.max(0, fillH - 12)} rx="2.5"
          fill="rgba(255,255,255,0.18)" clip-path="url(#{clipId})" />
  {/if}

  <!-- Top dome -->
  <ellipse cx={W / 2} cy={bodyY} rx={bodyW / 2} ry="10"
           fill="#1a1613" stroke="#4a3d2e" stroke-width="1.5" />

  <!-- Brass pressure post -->
  <rect x={W / 2 - 7} y={bodyY - 16} width="14" height="18" rx="3"
        fill="url(#{brassGrad})" />
  <rect x={W / 2 - 9} y={bodyY - 18} width="18" height="4" rx="1"
        fill="#e8a020" />

  <!-- Bottom ring -->
  <ellipse cx={W / 2} cy={bodyY + bodyH} rx={bodyW / 2} ry="8"
           fill="#1a1613" stroke="#4a3d2e" stroke-width="1.5" />

  <!-- Empty X -->
  {#if isEmpty}
    <g stroke="#3a3228" stroke-width="3" stroke-linecap="round" opacity="0.6">
      <line x1={bodyX + 20} y1={bodyY + 30} x2={bodyX + bodyW - 20} y2={bodyY + bodyH - 30} />
      <line x1={bodyX + bodyW - 20} y1={bodyY + 30} x2={bodyX + 20} y2={bodyY + bodyH - 30} />
    </g>
  {/if}
</svg>

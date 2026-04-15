<!-- frontend/src/lib/KegSvg.svelte -->
<script>
  export let color = '#C8860A';
  export let status = 'empty';   // empty | conditioning | on_tap | archived

  // Fill level by status
  const fillMap = { empty: 0, conditioning: 85, on_tap: 70, archived: 20 };
  $: fillPercent = fillMap[status] ?? 0;
  $: isActive = status !== 'empty' && status !== 'archived';
  $: fillColor = isActive ? color : '#444';
  $: opacity = status === 'archived' ? 0.45 : 1;

  // SVG dimensions
  const W = 80, H = 140;
  const bodyY = 20, bodyH = 100, bodyW = 60, bodyX = 10;
  $: fillH = (bodyH * fillPercent) / 100;
  $: fillY = bodyY + bodyH - fillH;
</script>

<svg width={W} height={H} viewBox="0 0 {W} {H}" style="opacity:{opacity}">
  <defs>
    <clipPath id="keg-clip-{status}-{color.replace('#','')}">
      <rect x={bodyX} y={fillY} width={bodyW} height={fillH} />
    </clipPath>
  </defs>

  <!-- Keg body outline -->
  <rect x={bodyX} y={bodyY} width={bodyW} height={bodyH} rx="8"
        fill="#333" stroke="#555" stroke-width="2"/>

  <!-- Liquid fill -->
  {#if fillPercent > 0}
    <rect x={bodyX} y={bodyY} width={bodyW} height={bodyH} rx="8"
          fill={fillColor}
          clip-path="url(#keg-clip-{status}-{color.replace('#','')})"
          style="transition: all 0.6s ease"/>
    <!-- Shine -->
    <rect x={bodyX + 8} y={fillY + 4} width="6" height={fillH - 8} rx="3"
          fill="rgba(255,255,255,0.15)"
          clip-path="url(#keg-clip-{status}-{color.replace('#','')})"/>
  {/if}

  <!-- Dome top -->
  <ellipse cx={W/2} cy={bodyY} rx={bodyW/2} ry="10"
           fill="#3a3a3a" stroke="#555" stroke-width="2"/>

  <!-- Pressure post (top) -->
  <rect x={W/2 - 5} y="4" width="10" height="14" rx="3"
        fill="#666" stroke="#888" stroke-width="1"/>

  <!-- Handles (left & right) -->
  <path d="M{bodyX - 8},{bodyY + 20} Q{bodyX - 16},{bodyY + 35} {bodyX - 8},{bodyY + 50}"
        fill="none" stroke="#555" stroke-width="4" stroke-linecap="round"/>
  <path d="M{bodyX + bodyW + 8},{bodyY + 20} Q{bodyX + bodyW + 16},{bodyY + 35} {bodyX + bodyW + 8},{bodyY + 50}"
        fill="none" stroke="#555" stroke-width="4" stroke-linecap="round"/>

  <!-- Bottom ring -->
  <ellipse cx={W/2} cy={bodyY + bodyH} rx={bodyW/2} ry="8"
           fill="#3a3a3a" stroke="#555" stroke-width="2"/>

  <!-- Liquid surface ripple (only when filled) -->
  {#if fillPercent > 5}
    <ellipse cx={W/2} cy={fillY} rx={bodyW/2 - 2} ry="4"
             fill={fillColor} opacity="0.6"/>
  {/if}
</svg>

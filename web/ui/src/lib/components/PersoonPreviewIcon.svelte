<script lang="ts">
  let {
    ontrigger,
    onrelease,
    onclick,
  }: {
    ontrigger: (e: MouseEvent | FocusEvent) => void;
    onrelease: () => void;
    onclick?: (e: MouseEvent) => void;
  } = $props();
</script>

<button
  type="button"
  class="preview-icon"
  aria-label="Voorvertoning"
  title="Voorvertoning"
  onmouseenter={ontrigger}
  onmouseleave={onrelease}
  onfocus={ontrigger}
  onblur={onrelease}
  onclick={(e) => {
    e.preventDefault();
    e.stopPropagation();
    onclick?.(e);
  }}
>
  <svg viewBox="0 0 20 20" width="16" height="16" aria-hidden="true">
    <path
      fill="currentColor"
      d="M10 4.5C5.5 4.5 2 10 2 10s3.5 5.5 8 5.5 8-5.5 8-5.5-3.5-5.5-8-5.5zm0 9a3.5 3.5 0 1 1 0-7 3.5 3.5 0 0 1 0 7z"
    />
  </svg>
</button>

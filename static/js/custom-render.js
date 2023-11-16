Object.assign(render, {
  media_file_guid_links: function render(data, type, full, meta, fieldOptions) {
    // Render a list of media files to a string of links to media files
    return data.map(
      guid => `<a href="../media-file/detail/${guid}"> ${guid} </a>`
    )
  },

  media_file_count: function render(data, type, full, meta, fieldOptions) {
    // Render a count of media files
    return data.length
  },

  sony_ci_asset_thumbnail: function render(data, type, full, meta, fieldOptions) {
    return data
      ? `<img src="${data.location}" style="max-height:150px;" loading="lazy">`
      : null
  },

  finished: function render(data, type, full, meta, fieldOptions) {
    if (data == null) return null_column();
    data = Array.isArray(data) ? data : [data];
    if (data.length == 0) return empty_column();
    return `<div class="d-flex">${data
      .map((d) =>
        d === true
          ? `<div class="p-1"><span class="text-center text-info"><i class="fa-solid fa-check fa-lg"></i></span></div>`
          : `<div class="p-1"><span class="text-center text-secondary"><i class="fa-solid fa-clock fa-lg"></i></span></div>`
      )
      .join("")}</div>`;
  },
  successful: function render(data, type, full, meta, fieldOptions) {
    if (data == null) return null_column();
    data = Array.isArray(data) ? data : [data];
    if (data.length == 0) return empty_column();
    return `<div class="d-flex">${data
      .map((d) =>
        d === true
          ? `<div class="p-1"><span class="text-center text-success"><i class="fa-solid fa-check-circle fa-lg"></i></span></div>`
          : `<div class="p-1"><span class="text-center text-danger"><i class="fa-solid fa-circle-xmark fa-lg"></i></span></div>`
      )
      .join("")}</div>`;
  },

  metaflow_pathspec_link: function render(data, type, full, meta, fieldOptions) {
    return `<a href="${data}">${data.split('https://mario.wgbh-mla.org/')[1]}
    <i class="fa fa-external-link" aria-hidden="true"></i></a>`;
  },

  metaflow_link: function render(data, type, full, meta, fieldOptions) {
    return `<a href="${data}">${data.split('/').pop()}
    <i class="fa fa-external-link" aria-hidden="true"></i></a>`;
  },
})

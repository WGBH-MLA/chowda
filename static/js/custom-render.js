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

  sony_ci_asset_thumbnail: function render(
    data,
    type,
    full,
    meta,
    fieldOptions
  ) {
    return data
      ? `<img src="${data.location}" style="max-height:150px;" loading="lazy">`
      : null
  },
})

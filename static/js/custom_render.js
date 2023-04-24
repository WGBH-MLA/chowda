Object.assign(render, {
  media_file_guid_links: function render(data, type, full, meta, fieldOptions) {
    // Render a list of media files to a string of links to media files
    return data.map(
      media_file =>
        `<a href="../media-file/detail/${
          media_file.id
        }"> ${media_file.guid.replace(/^cpb-aacip-/, '')} </a>`
    )
  },
  media_file_count: function render(data, type, full, meta, fieldOptions) {
    // Render a count of media files
    return data.length
  },
})

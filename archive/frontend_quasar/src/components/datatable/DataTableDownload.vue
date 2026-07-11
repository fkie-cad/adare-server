<template>
    <q-btn
      color="primary"
      icon="get_app"
      @click="DownloadFile(data, ExtractFilenameFromUrl(data))"
      class="q-px-sm q-mx-sm"
    >
      <q-tooltip>download</q-tooltip>
    </q-btn>
</template>

<script lang="ts">
import axios from 'axios';
import { exportFile } from 'quasar';

export default {
  name: 'DataTableDownload',
  components: {  },
  props: {
    data: {
      type: String,
      required: true,
    },
    row: {
      type: Object,
      required: true,
    }
  },

  setup() {

    function ExtractFilenameFromUrl(url: string): string {
      // Split the URL by '/' to get the segments
      const splittedFilename = url.split('/');

      if (splittedFilename.length === 0) {
        return '';
      }
      const lastSegment = splittedFilename.pop();
      if (!lastSegment) {
        return '';
      }

      // Get the filename and strip any fragment (#) or query parameters (?)
      const filename = lastSegment.split('#')[0].split('?')[0];

      // Return 'file' if the filename is empty, otherwise return the filename
      return filename || 'file';
    }

    function DownloadFile(url: string, filename: string) {
      axios.get(url, {responseType: 'blob'}).then((response) => {
        exportFile(filename, response.data)
      })
    }

    return {
      DownloadFile,
      ExtractFilenameFromUrl
    }
  }

};
</script>

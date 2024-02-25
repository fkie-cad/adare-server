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

  setup(props) {

    function ExtractFilenameFromUrl(url: string) {
      const filename = url.split('/').pop().split('#')[0].split('?')[0];
      if (filename === '') {
        return 'file';
      }
      return filename;
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

<template>
  <div class="q-pa-lg tw-w-full">
    <q-card>
      <q-card-section class="row">
        <div class="col-4">
          <div class="tw-text-3xl">Logfile for:</div>
        </div>
        <div class="col">
          <div class="row tw-text-gray-600 tw-text-right">
            <div class="col">experiment name</div>
            <div class="col">experiment run uuid</div>
<!--            <div class="col">experiment run status</div>-->
          </div>
          <div class="row tw-text-right">
            <div class="col tw-text-xl">{{experimentrun_data.experiment}}</div>
            <div class="col tw-text-xl">{{experimentrun_data.uuid}}</div>
<!--            <div class="col">-->
<!--              <q-icon-->
<!--                name="check_circle"-->
<!--                color="positive"-->
<!--                v-if="experimentrun_data.status.name == 'success'"-->
<!--                size="32px"-->
<!--              ><q-tooltip>success</q-tooltip></q-icon>-->
<!--              <q-icon-->
<!--                name="cancel"-->
<!--                color="negative"-->
<!--                v-if="experimentrun_data.status.name == 'failed'"-->
<!--                size="32px"-->
<!--              ><q-tooltip>failed</q-tooltip></q-icon>-->
<!--            </div>-->
          </div>
        </div>
      </q-card-section>
      <q-separator />
      <q-card-section>
        <div class="q-ma-lg q-gutter-md tw-border-2 tw-rounded tw-leading-tight tw-bg-slate-50">
          <div
            v-for="(row, index) in logfile_data.split('\n')"
            v-bind:key=index
            class="q-ma-xs"
          >
            {{row}}
          </div>
        </div>
      </q-card-section>
    </q-card>
  </div>
</template>

<script lang="ts">
import {onMounted, ref} from 'vue';
import axios from 'axios';
import API from 'src/api';

export default {
  name: 'LogFile',

  components: {},

  props: {
    experimentrunuuid: {
      type: String,
      required: true,
    }
  },

  setup(props) {

    let logfile_data = ref('')
    let experimentrun_data = ref({})

    onMounted(async () => {
      // load experimentrun data
      const response = await axios.get(API.API + 'experimentrun/experimentrun_' + props.experimentrunuuid)
      experimentrun_data.value = response.data
      // get logfile url
      const logfile_url = response.data.logfile

      // load logfile data
      let full_logfile_url = API.SERVER_URL + logfile_url
      const response2 = await axios.get(full_logfile_url)
      logfile_data.value = response2.data
    })

    return {
      logfile_data,
      experimentrun_data,
    }
  }
}

</script>

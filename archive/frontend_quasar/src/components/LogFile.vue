<!--<template>-->
<!--  <div class="q-pa-lg tw-w-full">-->
<!--    <q-card>-->
<!--      <q-card-section class="row">-->
<!--        <div class="col-4">-->
<!--          <div class="tw-text-3xl">Logfile for:</div>-->
<!--        </div>-->
<!--        <div class="col">-->
<!--          <div class="row tw-text-gray-600 tw-text-right">-->
<!--            <div class="col">experiment name</div>-->
<!--            <div class="col">experiment run uuid</div>-->
<!--&lt;!&ndash;            <div class="col">experiment run status</div>&ndash;&gt;-->
<!--          </div>-->
<!--          <div class="row tw-text-right">-->
<!--            <div class="col tw-text-xl">{{experimentrun_data.experiment}}</div>-->
<!--            <div class="col tw-text-xl">{{experimentrun_data.uuid}}</div>-->
<!--&lt;!&ndash;            <div class="col">&ndash;&gt;-->
<!--&lt;!&ndash;              <q-icon&ndash;&gt;-->
<!--&lt;!&ndash;                name="check_circle"&ndash;&gt;-->
<!--&lt;!&ndash;                color="positive"&ndash;&gt;-->
<!--&lt;!&ndash;                v-if="experimentrun_data.status.name == 'success'"&ndash;&gt;-->
<!--&lt;!&ndash;                size="32px"&ndash;&gt;-->
<!--&lt;!&ndash;              ><q-tooltip>success</q-tooltip></q-icon>&ndash;&gt;-->
<!--&lt;!&ndash;              <q-icon&ndash;&gt;-->
<!--&lt;!&ndash;                name="cancel"&ndash;&gt;-->
<!--&lt;!&ndash;                color="negative"&ndash;&gt;-->
<!--&lt;!&ndash;                v-if="experimentrun_data.status.name == 'failed'"&ndash;&gt;-->
<!--&lt;!&ndash;                size="32px"&ndash;&gt;-->
<!--&lt;!&ndash;              ><q-tooltip>failed</q-tooltip></q-icon>&ndash;&gt;-->
<!--&lt;!&ndash;            </div>&ndash;&gt;-->
<!--          </div>-->
<!--        </div>-->
<!--      </q-card-section>-->
<!--      <q-separator />-->
<!--      <q-card-section>-->
<!--        <div class="q-ma-lg q-gutter-md tw-border-2 tw-rounded tw-leading-tight tw-bg-slate-50">-->
<!--          <div-->
<!--            v-for="(row, index) in logfile_data.split('\n')"-->
<!--            v-bind:key=index-->
<!--            class="q-ma-xs"-->
<!--          >-->
<!--            {{row}}-->
<!--          </div>-->
<!--        </div>-->
<!--      </q-card-section>-->
<!--    </q-card>-->
<!--  </div>-->
<!--</template>-->

<!--<script lang="ts">-->
<!--import {onMounted, ref} from 'vue';-->
<!--import axios from 'axios';-->

<!--export default {-->
<!--  name: 'LogFile',-->

<!--  components: {},-->

<!--  props: {-->
<!--    experimentrunuuid: {-->
<!--      type: String,-->
<!--      required: true,-->
<!--    }-->
<!--  },-->

<!--  setup(props) {-->

<!--    let logfile_data = ref('')-->
<!--    let experimentrun_data = ref({})-->

<!--    onMounted(async () => {-->
<!--      // load experimentrun data-->
<!--      const response = await axios.get(API.API + 'experimentrun/experimentrun_' + props.experimentrunuuid)-->
<!--      experimentrun_data.value = response.data-->
<!--      // get logfile url-->
<!--      const logfile_url = response.data.logfile-->

<!--      // load logfile data-->
<!--      let full_logfile_url = API.SERVER_URL + logfile_url-->
<!--      const response2 = await axios.get(full_logfile_url)-->
<!--      logfile_data.value = response2.data-->
<!--    })-->

<!--    return {-->
<!--      logfile_data,-->
<!--      experimentrun_data,-->
<!--    }-->
<!--  }-->
<!--}-->

<!--</script>-->

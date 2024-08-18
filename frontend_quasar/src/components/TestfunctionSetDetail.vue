<template>
  <div
    v-if="experiment_data"
  >
    <q-card>
      <q-card-section>
        <div class="row tw-text-gray-600">
          <div class="col">name</div>
          <div class="col tw-text-right">uuid</div>
        </div>
        <div class="row  tw-text-3xl">
          <div class="col">{{experiment_data.name}}</div>
          <div class="col tw-text-right">{{experiment_data.uuid}}</div>
        </div>
      </q-card-section>
      <q-separator />
      <q-card-section class="row justify-between">
        <div class="col-8 q-pa-md">
          <q-card>
            <q-card-section class="tw-text-center tw-text-2xl bg-primary text-white q-pa-sm">
              Metadata
            </q-card-section>
            <q-separator/>
            <q-markup-table
              dense
            >
              <tbody>
              <tr>
                <td class="tw-text-left">publisher</td>
                <td>
                  <div class="tw-float-right">
                    <div class="tw-w-fit tw-h-fit q-py-md">
                      <div class="row bg-teal-1 tw-border-solid tw-rounded tw-border-2 tw-border-slate-400 q-pa-sm">
                        <div class="q-px-md tw-self-center">
                          {{ experiment_data.published_by.username }}
                        </div>
                        <ProfileImage
                          :username="experiment_data.published_by.username"
                          tooltip
                          linktoprofile
                          :avatar="experiment_data.published_by.avatar"
                        />
                      </div>
                    </div>
                  </div>
                </td>
              </tr>
              <tr>
                <td class="tw-text-left">publish date</td>
                <td class="tw-text-right">{{ experiment_data.published_at }}</td>
              </tr>
              <tr>
                <td class="tw-text-left">description</td>
                <td class="tw-text-right">
                  <div class="tw-whitespace-pre-wrap">
                    {{ experiment_data.description }}
                  </div>
                </td>
              </tr>
              <tr>
                <td class="tw-text-left">tags</td>
                <td class="tw-text-right">
                  <div class="tw-whitespace-pre-wrap">
                    <q-chip
                      v-for="tag in experiment_data.tags"
                      :key="tag"
                      :label="'#'+tag"
                      color="primary"
                      text-color="white"
                      class="q-ma-xs"
                    />
                  </div>
                </td>
              </tr>
              </tbody>
            </q-markup-table>
          </q-card>
        </div>
        <div class="col-4  q-pa-md tw-justify-end">
<!--          <div class="row">-->
<!--            <q-card class="tw-w-full">-->
<!--              <q-card-section class="tw-text-center tw-text-2xl bg-primary text-white q-pa-sm">-->
<!--                Os Information-->
<!--              </q-card-section>-->
<!--              <q-separator/>-->
<!--              <q-markup-table-->
<!--                dense-->
<!--              >-->
<!--                <tbody>-->
<!--                <tr>-->
<!--                  <td class="tw-text-left">Os</td>-->
<!--                  <td class="tw-text-right">{{ experiment_data.os_info.os }}</td>-->
<!--                </tr>-->
<!--                <tr>-->
<!--                  <td class="tw-text-left">Version</td>-->
<!--                  <td class="tw-text-right">{{ experiment_data.os_info.version }}</td>-->
<!--                </tr>-->
<!--                <tr>-->
<!--                  <td class="tw-text-left">Distribution</td>-->
<!--                  <td class="tw-text-right">{{ experiment_data.os_info.distribution }}</td>-->
<!--                </tr>-->
<!--                <tr>-->
<!--                  <td class="tw-text-left">Architecture</td>-->
<!--                  <td class="tw-text-right">{{ experiment_data.os_info.architecture }}</td>-->
<!--                </tr>-->
<!--                <tr>-->
<!--                  <td class="tw-text-left">Language</td>-->
<!--                  <td class="tw-text-right">{{ experiment_data.os_info.language }}</td>-->
<!--                </tr>-->
<!--                </tbody>-->
<!--              </q-markup-table>-->
<!--            </q-card>-->
<!--          </div>-->
          <div class="row q-mt-xl">
            <q-card class="tw-w-full">
              <q-card-section class="tw-text-center tw-text-2xl bg-primary text-white q-pa-sm">
                Runs
              </q-card-section>
              <q-separator/>
              <q-markup-table
                dense
              >
                <thead>
                <tr>
                  <th>
                    <q-icon
                      name="check_circle"
                      color="positive"
                      size="32px"
                    />
                  </th>
                  <th>
                    <q-icon
                      name="cancel"
                      color="negative"
                      size="32px"
                    />
                  </th>
                </tr>
                </thead>
                <tbody class="tw-text-center">
                <tr>
                  <td><div class="tw-text-2xl">{{ experiment_data.run_counts.successful }}</div></td>
                  <td><div class="tw-text-2xl">{{ experiment_data.run_counts.failed }}</div></td>
                </tr>
                </tbody>

              </q-markup-table>
            </q-card>
          </div>
        </div>
      </q-card-section>
      <q-card-section>
        <AdvancedDataTable
          :data_get_function="GetAbstractTests"
          :visible-columns="vis_columns_test"
          :columns="columns_test"
          title="Tests"
          class="tw-w-full"
        />
      </q-card-section>
      <q-card-section>
        <ExperimentrunTable
          :experiment="experiment_data.uuid"
        />
      </q-card-section>
    </q-card>
  </div>
</template>


<script lang="ts">
import { useExperimentStore } from 'stores/experiments';
import {storeToRefs} from 'pinia';
import {onMounted, ref} from 'vue';
import {Experiment} from 'src/datatypes/scenario';
import AdvancedDataTable from 'components/global/AdvancedDataTable.vue';
import ExperimentrunTable from 'components/ExperimentrunTable.vue';
import ProfileImage from 'components/ProfileImage.vue';

const columns_test = [
  { name: 'uuid', label: 'uuid', field: 'uuid', align: 'left', sortable: true, hideable: true, },
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: true },
  { name: 'description', label: 'description', field: 'description', align: 'left', sortable: true, hideable: true, },
  { name: 'testfunction', label: 'testfunction', field: 'testfunction', align: 'left', sortable: true, hideable: true, type: 'testfunction'},
  { name: 'parameters', label: 'parameters', field: 'parameters', align: 'left', sortable: true, hideable: true, type: 'testparameterentry' },
  { name: 'tool__name', label: 'tool name', field: 'tool__name', align: 'left', sortable: true, hideable: true, type: 'subparameter', subparameter: 'command' },
  { name: 'tool__command', label: 'tool command', field: 'tool__command', align: 'left', sortable: true, hideable: true, type: 'subparameter', subparameter: 'command'},
]

const vis_columns_test = ['name', 'description', 'testfunction', 'parameters', 'tool__name', 'tool__command']

export default {
  name: 'ExperimentOverview',

  components: {AdvancedDataTable, ProfileImage, ExperimentrunTable},

  props: {
    uuid: {
      type: String,
      required: true,
    },
  },

  setup(props) {
    let ExperimentStore = useExperimentStore()
    storeToRefs(ExperimentStore)

    let experiment_data = ref<Experiment>()

    onMounted(async () => {
      await ExperimentStore.LoadExperiment(props.uuid)
      experiment_data.value = ExperimentStore.GetExperiment(props.uuid)
      console.log(experiment_data.value)
    })

    return {
    }
  }
}

</script>

<template>
  <div v-if="testfunctionSet" class="full-width q-pa-xl">
    <q-card
      class="full-width"
    >
      <q-card-section>
        <div class="row tw-text-gray-600">
          <div class="col">name</div>
          <div class="col tw-text-right">published by</div>
        </div>
        <div class="row  tw-text-3xl">
          <div class="col">{{testfunctionSet.name}}</div>
          <div class="col flex justify-end"><UserAvatar :user="testfunctionSet.published_by"/></div>
        </div>
        <div class="row tw-text-gray-600 q-pt-md">
          <div class="col"># testfunctions</div>
          <div class="col tw-text-right">accepted by</div>
        </div>
        <div class="row  tw-text-3xl">
          <div class="col">{{testfunctionSet.num_testfunctions}}</div>
          <div class="col flex justify-end">
            <UserAvatar :user="testfunctionSet.accepted_by" v-if="testfunctionSet.accepted_by"/>
            <div class="tw-text-3xl">-</div>
          </div>
        </div>
        <div class="row tw-text-gray-600 q-pt-md" v-if="testfunctionSet.description">
          <div class="col">description</div>
          <div class="col tw-text-right"></div>
        </div>
        <div class="row  tw-text-3xl" v-if="testfunctionSet.description">
          <div class="col">{{testfunctionSet.description}}</div>
          <div class="col"></div>
        </div>
        <div class="row tw-text-gray-600 q-pt-md">
          <div class="col">files</div>
          <div class="col tw-text-right"></div>
        </div>
        <div class="row tw-text-3xl">
          <div class="col">
            <q-btn
              color="primary"
              icon="open_in_new"
              @click="openGiteaTestfunctionSetDir"
            />
          </div>
          <div class="col"></div>
        </div>
      </q-card-section>
      <q-separator />
      <q-card-section>
        <DataTable title="Testfunctions" :store="testfunctionStore" :columns="columns" />
      </q-card-section>
    </q-card>
  </div>
  <div v-else>
    <h1>
      Testfunction with name {{ name }} not found
    </h1>
  </div>
</template>

<script lang="ts">
import { computed, onMounted } from 'vue';
import { useTestfunctionSetStore } from 'src/store/testfunctionset';
import { useTestfunctionStore } from 'src/store/testfunction';
import DataTable from 'components/datatable/DataTable.vue';
import { CustomQTableColumn } from 'src/models/quasar_extensions';
import UserAvatar from 'components/global/UserAvatar.vue';

const columns: CustomQTableColumn[] = [
  { name: 'name', label: 'name', field: 'name', align: 'left', sortable: true, visible: true, hideable: true},
  { name: 'description', label: 'description', field: 'description', align: 'left', sortable: true, visible: true, hideable: true},
  { name: 'possible_parameters', label: 'possible_parameters', field: 'possible_parameters', align: 'left', sortable: true, visible: true, hideable: true},
]


export default {
  name: 'TestfunctionSetDetail',
  components: { DataTable , UserAvatar},
  props: {
    name: {
      type: String,
      required: true,
    },
  },

  setup(props) {
    const store = useTestfunctionSetStore();
    const testfunctionStore = useTestfunctionStore();
    testfunctionStore.setTestfunctionSet(props.name);
    const testfunctionSet = computed(() => store.getTestfunctionSet(props.name));

    const openGiteaTestfunctionSetDir = () => {
      const file = testfunctionSet.value?.file
      const parentDir = file?.split('/').slice(0, -1).join('/')
      window.open(parentDir, '_blank')
    }

    onMounted(async () => {
      await store.fetchTestfunctionSets('');
    });

    return {
      columns,
      testfunctionStore,
      testfunctionSet,
      openGiteaTestfunctionSetDir,
    };
  }
};
</script>

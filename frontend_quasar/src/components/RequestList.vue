<template>
  <div
    class="tw-w-5/6"
  >
    <RequestTable />
  </div>
</template>


<script lang="ts">
import RequestTable from 'components/RequestTable.vue';


export default {
  name: 'RequestList',
  components: {RequestTable},
}

</script>

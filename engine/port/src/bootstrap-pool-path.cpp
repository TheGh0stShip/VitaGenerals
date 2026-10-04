// SPDX-License-Identifier: GPL-3.0-or-later
#ifndef GENERALS_MEMORY_POOL_CONFIG_PATH
#error Define the bootstrap memory-pool configuration path explicitly
#endif
namespace { constexpr char poolConfigPath[] = GENERALS_MEMORY_POOL_CONFIG_PATH; }
const char* platformMemoryPoolConfigPath() { return poolConfigPath; }

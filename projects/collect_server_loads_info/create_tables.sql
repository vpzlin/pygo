-- 表: 服务器列表create table if not exists server_list(    server     varchar(19)               -- 服务器IP或服务器名   ,enable     int                       -- 是否可用: 0否, 1是   ,username   varchar(20)               -- 用户名   ,password   varchar(100)              -- 密码   ,create_dt  date                      -- 记录创建时间   ,remark     varchar(400)              -- 备注   ,primary key(server));
-- 表: 服务器负载create table if not exists server_loads(    scan_dt                         varchar(19)       -- 扫描时间   ,server                          varchar(100)      -- 服务器IP或服务器名   ,is_succeed                      int               -- 是否扫描成功:1为成功,0为失败
   ,create_dt                       date              -- 记录创建时间
   ,remark                          varchar(400)      -- 备注
   ,disk_all_mounted_total_kb       real
   ,disk_all_mounted_used_kb        real
   ,disk_all_mounted_available_kb   real
   ,disk_all_mounted_used_percent   real
   ,disk_detail                     varchar(4000)
   ,net_receive_bytes               real
   ,net_receive_packets             real
   ,net_receive_errs                real
   ,net_receive_drop                real
   ,net_receive_fifo                real
   ,net_receive_frame               real
   ,net_receive_compressed          real
   ,net_receive_multicast           real
   ,net_transmit_bytes              real
   ,net_transmit_packets            real
   ,net_transmit_errs               real
   ,net_transmit_drop               real
   ,net_transmit_fifo               real
   ,net_transmit_colls              real
   ,net_transmit_carrier            real
   ,net_transmit_compressed         real
   ,mem_total_mb                    real
   ,mem_used_mb                     real
   ,mem_free_mb                     real
   ,mem_shared_mb                   real
   ,mem_buff_cache_mb               real
   ,mem_available_mb                real
   ,mem_swap_total_mb               real
   ,mem_swap_used_mb                real
   ,mem_swap_free_mb                real
   ,cpu_us_max                      real
   ,cpu_us_min                      real
   ,cpu_us_avg                      real
   ,cpu_sy_max                      real
   ,cpu_sy_min                      real
   ,cpu_sy_avg                      real
   ,cpu_ni_max                      real
   ,cpu_ni_min                      real
   ,cpu_ni_avg                      real
   ,cpu_id_max                      real
   ,cpu_id_min                      real
   ,cpu_id_avg                      real
   ,cpu_wa_max                      real
   ,cpu_wa_min                      real
   ,cpu_wa_avg                      real
   ,cpu_hi_max                      real
   ,cpu_hi_min                      real
   ,cpu_hi_avg                      real
   ,cpu_si_max                      real
   ,cpu_si_min                      real
   ,cpu_si_avg                      real
   ,cpu_st_max                      real
   ,cpu_st_min                      real
   ,cpu_st_avg                      real
   ,uptime_load_average_15min       real
   ,uptime_load_average_5min        real
   ,uptime_load_average_1min        real
   ,uptime_user_connections         real
   ,result_uptime_runtime           real
   ,hostname                        varchar(400)   ,primary key(scan_dt, server));


